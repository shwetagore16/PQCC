# PQCC (Post Quantum Cryptography Checker) - Team Doc

This document explains how PQC works in the project, the tools/services needed, and the end-to-end backend and frontend workflow.

## 1) What the system does
PQCC is a full-stack platform to inventory cryptography, analyze post-quantum risk, and track readiness with CBOM (Cryptography Bill of Materials) data. It collects assets, runs scans or CBOM uploads, scores risk, and renders dashboards for compliance and migration planning.

Key capabilities:
- Asset ingestion and discovery
- CBOM generation and storage
- PQC scoring and readiness classification
- Compliance labeling and playbooks
- Risk and forecast dashboards

## 2) High-level architecture
Services and roles:
- Frontend: React + Vite (dashboard UI)
- Backend: FastAPI (REST APIs)
- DB: PostgreSQL (assets, scans, CBOM records)
- Redis + Celery: background discovery/scanning tasks
- Neo4j: topology graph (optional)
- ML engine: HNDL scoring, forecasting, GNN attack path (optional)

Architecture diagram (paste into Word as monospace text):

[
  User / Analyst
    |
    v
  React + Vite Frontend
    |
    v
  FastAPI Backend (API Gateway)
   |       |        |         \
   |       |        |          \
   v       v        v           v
PostgreSQL Redis  Neo4j      ML Engine
  (Assets, (Broker) (Topology) (HNDL/Forecast/GNN)
   CBOM)
    |
    v
     Celery Workers
  (Discovery, TLS, CBOM)
]

Data flow summary:
1) Asset ingestion (seed domains or scans)
2) CBOM data arrives (upload or derived from scans)
3) PQC engine analyzes CBOM and outputs risk
4) Backend persists results to Postgres
5) Frontend polls and renders dashboards

End-to-end flow diagram (paste into Word as monospace text):

[
  Seed Domains / CBOM Upload
    |
    v
  FastAPI /api/v1/assets
    |
    v
   Parse CBOM -> PQC Engine
    |
    v
  Store CBOM + Update Asset
    |
    v
  Frontend Polls /assets + /cbom
    |
    v
     Dashboards & Reports
]

## 3) PQC engine - how scoring works
The PQC engine consumes CBOM components and evaluates cryptographic properties:
- Protocol/TLS version
- Cipher suite
- Key exchange
- Signature algorithm
- Key size / certificate algorithm

It computes:
- pqc_status: PQC_READY | HYBRID | VULNERABLE
- risk_score: numeric risk (0-100 from engine, normalized to 0-10 in asset)
- weak_points: list of weak algorithms
- recommendations: migration hints
- future_risk and agility

Scoring is dynamic and can adjust weights based on CBOM metadata (exposure, classification, environment, asset_type).

## 4) Backend workflow
### 4.1 Asset ingestion
Endpoint: POST /api/v1/assets/seed-domains
- Creates MasterAsset rows
- Optionally dispatches discovery tasks (Celery)

### 4.2 PQC analysis
Endpoint: GET /api/v1/assets/{id}/pqc
- If asset is UUID and CBOM exists, it analyzes stored CBOM components
- If asset is non-UUID or CBOM missing, it falls back to mock CBOM

### 4.3 CBOM upload
Endpoint: POST /api/v1/assets/{id}/cbom
- Accepts CycloneDX-like CBOM data
- Runs PQC analysis
- Stores CBOM records in Postgres
- Updates MasterAsset risk_score and status

CBOM upload flow (paste into Word as monospace text):

[
  UI: AssetManagementPage
    |
    v
  POST /assets/{id}/cbom
    |
    v
  PQC Engine (analyze_cbom)
    |
    v
  Persist CBOMRecord + Update Asset
    |
    v
  UI refresh (poll + localStorage event)
]

### 4.4 CBOM records listing
Endpoint: GET /api/v1/cbom
- Returns stored CBOM records for dashboards

### 4.5 Optional services
- Neo4j can be disabled with NEO4J_ENABLED=false
- Postgres warmup can be disabled with POSTGRES_ENABLED=false

## 5) Frontend workflow
### 5.1 API client
All API calls go through frontend/src/api/client.ts
Base URL is VITE_API_URL (defaults to http://localhost:8000)

### 5.2 Live updates
- Asset Management page uploads CBOM and pushes update to localStorage + custom event
- PQC Classification page listens to updates and merges with live assets
- Dashboards poll every 20 seconds for fresh data

### 5.3 Key pages
- DashboardPage: summary widgets from /assets
- AssetManagementPage: asset list, PQC status, CBOM upload
- PQCClassificationPage: risk assets and readiness
- CBOMRecordsPage: CBOM inventory from /cbom
- RiskAnalysisPage: pulls top-risk asset and score

## 6) Required tools and services
### 6.1 Local development tools
- Python 3.11+
- Node.js 18+
- Docker + Docker Compose

### 6.2 Services (recommended for real data)
- PostgreSQL (required for persistence)
- Redis (required for Celery tasks)
- Celery workers (scan/discovery tasks)
- Neo4j (optional graph features)

## 7) Local setup (quick)
Backend:
1) cd backend
2) python -m venv .venv
3) .\.venv\Scripts\Activate.ps1
4) pip install -r requirements.txt
5) alembic upgrade head
6) uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Frontend:
1) cd frontend
2) npm install
3) npm run dev

## 8) Environment variables
Backend (.env):
- POSTGRES_SERVER, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
- POSTGRES_ENABLED=true|false
- NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
- NEO4J_ENABLED=true|false
- REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND

Frontend (Vercel or .env.local):
- VITE_API_URL=http://localhost:8000 (local) or https://<your-backend-host>

## 9) Deployment notes
- Vercel deploys only the frontend
- Backend must be deployed separately (Render/Railway/Fly/etc.)
- Set VITE_API_URL to backend base URL in Vercel

## 10) Testing and validation
- Backend docs: http://localhost:8000/api/v1/docs
- Smoke tests:
  - POST /assets/seed-domains
  - POST /assets/{id}/cbom
  - GET /assets
  - GET /cbom

## 11) Common troubleshooting
- 500 on seed-domains with auto_scan=true: Redis/Celery not running
- Vercel build fail: set root directory to frontend, build command npm run build, output dist
- Frontend cannot reach backend: set correct VITE_API_URL

## 12) Repo structure
backend/   FastAPI app, workers, models, services
frontend/  React dashboard
ml_engine/ ML utilities
k8s/       Kubernetes manifests
deploy/    Nginx config
UI_WIREFRAMES/ UI reference

---

## 13) Advanced PQC Intelligence Upgrade (Plan)
Goal: add AI/ML-driven scoring without breaking existing endpoints, UI updates, or localStorage event flow.

Phase 1 - Backend scoring modules (non-breaking):
1) Add advanced scoring module for HNDL + Crypto Agility.
2) Add policy engine (NIST + TLS deprecation rules).
3) Add ML classifier for PQC Ready vs Not Ready with confidence.
4) Add remediation prioritizer.

Phase 2 - API extension:
1) Extend /assets/{id}/pqc response with new fields only.
2) Add new /assets/{id}/report endpoint (PDF + JSON).

Phase 3 - Frontend:
1) Show HNDL + Crypto Agility on dashboards.
2) Show False Positive flag and ML confidence in asset details.
3) Add Download Report button.

Phase 4 - Tests and performance:
1) Unit tests for scoring, ML, and report generation.
2) Add caching and batch processing.

## 14) HNDL Score (Harvest Now Decrypt Later)
Inputs:
- data_sensitivity: critical | internal | public
- encryption_type: RSA | ECC | PQC | Hybrid
- key_size: integer
- exposure: internet | internal
- retention_years: integer

Weights (example, configurable):
- sensitivity: 0.25
- encryption_type: 0.25
- key_size: 0.20
- exposure: 0.20
- retention: 0.10

Formula (transparent):
HNDL = sum(param_score_i * weight_i)
Output: 0-100

## 15) Crypto Agility Score
Inputs:
- algorithm_flexibility: hardcoded | upgradeable
- key_rotation: true | false
- tls_version: TLS 1.0/1.1/1.2/1.3
- hybrid_support: true | false
- cert_upgrade_ease: low | medium | high

Weights (example, configurable):
- flexibility: 0.30
- rotation: 0.20
- tls: 0.20
- hybrid: 0.20
- cert: 0.10

Formula (transparent):
Agility = sum(param_score_i * weight_i)
Output: 0-100

## 16) False Positive Detection (ML)
Model: Logistic Regression (fast, interpretable) or Random Forest (better accuracy).

Feature set (from CBOM):
- tls_version
- key_exchange_type
- signature_algorithm
- key_size
- cipher_family
- certificate_algorithm

Logic:
1) Predict ML label: PQC Ready | Not Ready
2) Compare with rule-based label
3) If mismatch, set false_positive_flag = true
4) Expose ml_confidence in API response

## 17) Policy and Future Risk Engine
Historical rules (examples):
- RSA < 2048 -> insecure
- TLS 1.0/1.1 -> deprecated

Future risk prediction (lightweight):
- RSA: high
- ECC: medium
- Hybrid: medium-low
- PQC: low

Output:
- future_risk_score (0-100)
- drivers (rules that triggered)

## 18) Remediation Prioritization
Priority formula (example):
Priority = 0.40 * risk_score + 0.30 * hndl_score + 0.20 * exposure + 0.10 * business_criticality

Output:
- priority_level: High | Medium | Low
- suggested_action
- auto_fix_eligible: true | false

## 19) Report Generation
Endpoint: GET /api/v1/assets/{id}/report?format=pdf|json

Report contents:
- asset details
- pqc_status, risk_score
- hndl_score, crypto_agility_score
- weak_points, recommendations
- future_risk_score
- false_positive_flag + ml_confidence

PDF library: reportlab (backend)

## 20) Scalability and Caching
Recommendations:
- Cache PQC results by CBOM hash
- Batch scoring endpoint for multiple assets
- Async processing via Celery for heavy runs
- Avoid recomputation when CBOM unchanged

## 21) Testing Plan (Pytest)
Unit tests:
- CBOM parsing
- HNDL scoring
- Agility scoring
- Policy engine rule triggers
- ML classifier output + confidence

Integration tests:
- /assets/{id}/pqc returns new fields
- /assets/{id}/report returns PDF + JSON
- False positive flag logic


Contact: Add the project owner and team contact details here.
