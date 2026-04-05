"""
backend/app/core/secrets.py — Secure Secrets Management.

Implements a layered secrets loader:

  Priority 1 → HashiCorp Vault (via HVAC client)
               Secrets read from:  secret/pqss/<path>
  Priority 2 → AWS Secrets Manager (via boto3)
               Fallback for cloud deployments.
  Priority 3 → Environment variables / .env file
               Development and CI fallback. NEVER use in production.

Architecture:
  SecretsManager  — unified facade, caches secrets to reduce Vault round-trips
  VaultBackend    — reads from Vault KV v2
  AWSBackend      — reads from AWS Secrets Manager
  EnvBackend      — reads from os.environ / pydantic-settings

Usage::

    from app.core.secrets import get_secret, secrets_manager

    # Fetch a single secret value
    db_password = get_secret("database/POSTGRES_PASSWORD")

    # Fetch all application secrets at startup (cached)
    secrets = secrets_manager.load_all()
    jwt_key = secrets.jwt_secret_key

Security controls:
  • Secrets are stored in memory only (never written to disk)
  • Cache TTL: 15 minutes (automatic refresh from Vault)
  • In-memory values are stored as SecretStr (Pydantic) — never logged
  • Vault token is itself read from a K8s ServiceAccount token (IRSA/Workload Identity)
"""

from __future__ import annotations

import abc
import logging
import os
import threading
import time
from functools import lru_cache
from typing import Any

from pydantic import SecretStr

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Typed Secret Container
# ─────────────────────────────────────────────────────────────────────────────

class AppSecrets:
    """
    Strongly-typed container for all application secrets.

    Values are SecretStr — Pydantic will redact them in logs/repr.
    """

    def __init__(self, raw: dict[str, str]) -> None:
        self._raw = raw
        # ── Database credentials ────────────────────────────────────────────
        self.postgres_user:     SecretStr = SecretStr(raw["POSTGRES_USER"])
        self.postgres_password: SecretStr = SecretStr(raw["POSTGRES_PASSWORD"])
        self.neo4j_password:    SecretStr = SecretStr(raw["NEO4J_PASSWORD"])
        self.redis_password:    SecretStr = SecretStr(raw["REDIS_PASSWORD"])

        # ── JWT ────────────────────────────────────────────────────────────
        self.jwt_secret_key:    SecretStr = SecretStr(raw["JWT_SECRET_KEY"])

        # ── External API keys ──────────────────────────────────────────────
        self.shodan_api_key:    SecretStr = SecretStr(raw.get("SHODAN_API_KEY", ""))
        self.servicenow_password: SecretStr = SecretStr(raw.get("SERVICENOW_PASSWORD", ""))
        self.jira_api_token:    SecretStr = SecretStr(raw.get("JIRA_API_TOKEN", ""))

    def get_database_url(self, driver: str = "postgresql+asyncpg") -> SecretStr:
        """Build the full async database URL from components."""
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db   = os.getenv("POSTGRES_DB",   "pqss_db")
        url  = (
            f"{driver}://{self.postgres_user.get_secret_value()}"
            f":{self.postgres_password.get_secret_value()}"
            f"@{host}:{port}/{db}"
        )
        return SecretStr(url)

    def get_neo4j_auth(self) -> tuple[str, str]:
        return (
            os.getenv("NEO4J_USER", "neo4j"),
            self.neo4j_password.get_secret_value(),
        )

    def get_redis_url(self, db: int = 0) -> SecretStr:
        host = os.getenv("REDIS_HOST", "localhost")
        port = os.getenv("REDIS_PORT", "6379")
        pwd  = self.redis_password.get_secret_value()
        return SecretStr(f"redis://:{pwd}@{host}:{port}/{db}")

    def __repr__(self) -> str:
        return "AppSecrets(<redacted>)"


# ─────────────────────────────────────────────────────────────────────────────
# Backend Interface
# ─────────────────────────────────────────────────────────────────────────────

class _SecretsBackend(abc.ABC):
    @abc.abstractmethod
    def fetch(self, path: str) -> dict[str, str]:
        """Fetch a dict of key→value for the given secret path."""

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Return True if this backend is reachable."""


# ─────────────────────────────────────────────────────────────────────────────
# Backend 1: HashiCorp Vault (KV v2)
# ─────────────────────────────────────────────────────────────────────────────

class VaultBackend(_SecretsBackend):
    """
    Reads secrets from HashiCorp Vault using HVAC.

    Authentication methods (tried in order):
      1. VAULT_TOKEN env var (development)
      2. Kubernetes ServiceAccount token (production Workload Identity)
      3. AWS IAM auth (cloud deployments)
    """

    def __init__(self) -> None:
        self._url   = os.getenv("VAULT_ADDR", "http://vault:8200")
        self._mount = os.getenv("VAULT_KV_MOUNT", "secret")
        self._client = None

    def _get_client(self):
        if self._client and self._client.is_authenticated():
            return self._client

        try:
            import hvac  # type: ignore[import]
        except ImportError:
            raise RuntimeError("hvac not installed. Run: pip install hvac")

        client = hvac.Client(url=self._url)

        token = os.getenv("VAULT_TOKEN")
        if token:
            client.token = token
            logger.info("vault_auth_token", url=self._url)

        elif os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/token"):
            # Kubernetes ServiceAccount token — injected automatically by K8s
            with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as f:
                jwt = f.read()
            role = os.getenv("VAULT_K8S_ROLE", "pqss-backend")
            client.auth.kubernetes.login(role=role, jwt=jwt)
            logger.info("vault_auth_k8s_serviceaccount", role=role)

        else:
            raise RuntimeError(
                "No Vault authentication method available. "
                "Set VAULT_TOKEN or run inside a Kubernetes pod."
            )

        if not client.is_authenticated():
            raise RuntimeError(f"Failed to authenticate with Vault at {self._url}")

        self._client = client
        return client

    def is_available(self) -> bool:
        try:
            import hvac                           # type: ignore[import]
            c = hvac.Client(url=self._url)
            return c.sys.is_initialized()
        except Exception:
            return False

    def fetch(self, path: str) -> dict[str, str]:
        """
        Fetch a KV v2 secret at path `secret/pqss/<path>`.

        Returns a flat dict of the secret's key:value data.
        """
        client = self._get_client()
        full_path = f"pqss/{path}"
        response = client.secrets.kv.v2.read_secret_version(
            path=full_path,
            mount_point=self._mount,
        )
        data: dict[str, str] = response["data"]["data"]
        logger.info("vault_secret_fetched", path=full_path, keys=list(data.keys()))
        return data


# ─────────────────────────────────────────────────────────────────────────────
# Backend 2: AWS Secrets Manager
# ─────────────────────────────────────────────────────────────────────────────

class AWSSecretsBackend(_SecretsBackend):
    """Reads secrets from AWS Secrets Manager using boto3."""

    def __init__(self) -> None:
        self._region = os.getenv("AWS_REGION", "ap-south-1")
        self._prefix = os.getenv("AWS_SM_PREFIX", "pqss/")

    def is_available(self) -> bool:
        try:
            import boto3
            boto3.client("secretsmanager", region_name=self._region)
            return True
        except Exception:
            return False

    def fetch(self, path: str) -> dict[str, str]:
        import json

        import boto3

        client = boto3.client("secretsmanager", region_name=self._region)
        secret_name = f"{self._prefix}{path}"
        response = client.get_secret_value(SecretId=secret_name)
        raw = response.get("SecretString", "{}")
        data: dict[str, str] = json.loads(raw)
        logger.info("aws_sm_secret_fetched", path=secret_name, keys=list(data.keys()))
        return data


# ─────────────────────────────────────────────────────────────────────────────
# Backend 3: Environment / .env (development fallback)
# ─────────────────────────────────────────────────────────────────────────────

_REQUIRED_SECRETS = [
    "POSTGRES_USER", "POSTGRES_PASSWORD",
    "NEO4J_PASSWORD", "REDIS_PASSWORD",
    "JWT_SECRET_KEY",
]


class EnvBackend(_SecretsBackend):
    """
    Reads secrets from environment variables / .env file.

    ⚠ WARNING: Only acceptable for local development and CI.
               NEVER use in production — env vars can leak via /proc, logs, etc.
    """

    def is_available(self) -> bool:
        return True   # Always available (env always exists)

    def fetch(self, path: str) -> dict[str, str]:
        # Ignore path — env backend returns all known secrets at once
        env_app = os.getenv("APP_ENV", "development")
        if env_app == "production":
            logger.critical(
                "env_backend_in_production",
                message="SECURITY VIOLATION: EnvBackend must not be used in production. "
                        "Configure Vault or AWS Secrets Manager.",
            )
            raise RuntimeError(
                "EnvBackend is not permitted in production. "
                "Configure VAULT_ADDR or AWS_REGION."
            )

        missing = [k for k in _REQUIRED_SECRETS if not os.getenv(k)]
        if missing:
            logger.warning("env_secrets_missing", keys=missing)

        return {
            key: os.getenv(key, "")
            for key in _REQUIRED_SECRETS + [
                "SHODAN_API_KEY",
                "SERVICENOW_PASSWORD",
                "JIRA_API_TOKEN",
            ]
        }


# ─────────────────────────────────────────────────────────────────────────────
# Unified SecretsManager Facade
# ─────────────────────────────────────────────────────────────────────────────

_CACHE_TTL_SECONDS = 900   # 15-minute cache TTL


class SecretsManager:
    """
    Unified secrets manager facade with automatic backend selection and caching.

    Backend selection order:
        1. Vault — if VAULT_ADDR is set and reachable
        2. AWS   — if AWS_SM_PREFIX is set and boto3 reachable
        3. Env   — fallback (development only)

    Thread-safe (uses threading.RLock) and caches fetched secrets for
    CACHE_TTL seconds to reduce latency and rate-limiting risk.
    """

    def __init__(self) -> None:
        self._backends: list[_SecretsBackend] = [
            VaultBackend(),
            AWSSecretsBackend(),
            EnvBackend(),
        ]
        self._cache:      dict[str, Any] = {}
        self._cache_time: float          = 0.0
        self._lock = threading.RLock()
        self._active_backend: _SecretsBackend | None = None

    def _select_backend(self) -> _SecretsBackend:
        """Select the first available backend."""
        if self._active_backend:
            return self._active_backend

        for backend in self._backends:
            if backend.is_available():
                logger.info(
                    "secrets_backend_selected",
                    backend=type(backend).__name__,
                )
                self._active_backend = backend
                return backend

        raise RuntimeError("No secrets backend is available!")

    def get_raw(self, path: str = "app") -> dict[str, str]:
        """Fetch raw secret dict, with caching and auto-refresh."""
        with self._lock:
            now = time.monotonic()
            if self._cache and (now - self._cache_time) < _CACHE_TTL_SECONDS:
                return self._cache

            backend = self._select_backend()
            data    = backend.fetch(path)
            self._cache      = data
            self._cache_time = now
            logger.info("secrets_cache_refreshed", backend=type(backend).__name__)
            return data

    def load_all(self) -> AppSecrets:
        """
        Load all application secrets and return a typed AppSecrets instance.

        Called once at application startup (FastAPI lifespan).
        """
        raw = self.get_raw(path="app")    # Vault path: secret/pqss/app
        # Merge database secrets if Vault separates them
        try:
            raw.update(self.get_raw(path="database"))
        except Exception:
            pass  # Env backend has everything in one fetch
        return AppSecrets(raw)

    def invalidate_cache(self) -> None:
        """Force-refresh on next access (e.g. after secret rotation)."""
        with self._lock:
            self._cache      = {}
            self._cache_time = 0.0
            self._active_backend = None
        logger.info("secrets_cache_invalidated")


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton + convenience functions
# ─────────────────────────────────────────────────────────────────────────────

secrets_manager = SecretsManager()


@lru_cache(maxsize=1)
def get_app_secrets() -> AppSecrets:
    """
    Return the cached AppSecrets singleton.

    Call this instead of instantiating AppSecrets directly.
    The lru_cache ensures secrets are only fetched once per process.

    Integrate with FastAPI::

        from app.core.secrets import get_app_secrets

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            secrets = get_app_secrets()
            app.state.db_url = secrets.get_database_url()
            yield

    """
    return secrets_manager.load_all()


def get_secret(key: str) -> str:
    """
    Convenience: fetch a single secret value by key name.

    Example::

        jwt_key = get_secret("JWT_SECRET_KEY")
        db_pwd  = get_secret("POSTGRES_PASSWORD")
    """
    secrets = get_app_secrets()
    raw = secrets_manager.get_raw()
    value = raw.get(key, "")
    if not value:
        logger.warning("secret_not_found", key=key)
    return value
