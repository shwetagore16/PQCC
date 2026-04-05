"""
ml_engine/forecasting.py — HNDL Exposure Forecasting Pipeline.

Two complementary forecasting approaches:

1. Prophet Time-Series Decomposition
   ─────────────────────────────────
   Given a historical HNDL exposure time-series (one data-point per scan cycle),
   Prophet decomposes it into trend + seasonality components and projects
   forward by `forecast_horizon_years`.

   Output: P10/P50/P90 forecast bands over the forecast horizon.

2. Monte Carlo CRQC Arrival Simulation
   ─────────────────────────────────────
   10,000 simulation runs, each sampling:
     • Quantum arrival year: triangular distribution (2030–2040, mode=2033)
     • Migration velocity:   normal distribution (mean=T_migrate, sd=1.5y)
     • Harvest window:       uniform distribution [3, 8] years

   For each run: if T_harvest + T_decrypt < T_migrate → EXPOSURE = 1 (breach).
   Output: P10/P50/P90 breach-year bands and conditional breach probabilities.
"""

from __future__ import annotations

import warnings
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import structlog

from ml_engine.schemas import ForecastBand, ForecastResult, MonteCarloSummary

logger = structlog.get_logger(__name__)
warnings.filterwarnings("ignore", category=FutureWarning)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

_CURRENT_YEAR: int = datetime.utcnow().year

# CRQC arrival triangular distribution parameters (years)
CRQC_MIN:     float = 2028.0   # Earliest plausible
CRQC_MODE:    float = 2033.0   # Most likely (median NIST estimate)
CRQC_MAX:     float = 2045.0   # Latest plausible (pessimistic optimist)

# Migration duration — normal distribution (years)
MIGRATE_MEAN: float = 4.0
MIGRATE_STD:  float = 1.5

# Harvest window — uniform distribution (years)
HARVEST_MIN:  float = 3.0
HARVEST_MAX:  float = 8.0

# Simulation parameters
N_MC_RUNS:    int   = 10_000
RNG_SEED:     int   = 2026


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Prophet availability guard
# ─────────────────────────────────────────────────────────────────────────────

def _import_prophet():
    """Lazy import of Prophet — avoids hard coupling if not installed."""
    try:
        from prophet import Prophet  # type: ignore[import]
        return Prophet
    except ImportError as e:
        raise ImportError(
            "prophet is not installed. Run: pip install prophet"
        ) from e


# ─────────────────────────────────────────────────────────────────────────────
# Prophet Forecasting
# ─────────────────────────────────────────────────────────────────────────────

class HNDLProphetForecaster:
    """
    Prophet-based trend decomposition and multi-period HNDL forecasting.

    Usage::

        forecaster = HNDLProphetForecaster()
        bands = forecaster.forecast(
            history=time_series,        # list[{"ds": date_str, "y": hndl_float}]
            horizon_years=5,
        )
    """

    def __init__(
        self,
        changepoint_prior_scale: float = 0.15,
        seasonality_mode: str = "additive",
        weekly_seasonality: bool = False,
        yearly_seasonality: bool = True,
        interval_width: float = 0.80,   # 80% CI → P10/P90
    ) -> None:
        """
        Args:
            changepoint_prior_scale: Controls trend flexibility (higher = more flexible).
                                     HNDL series tend to be slowly evolving — keep this low.
            seasonality_mode:        'additive' or 'multiplicative'.
            interval_width:          Uncertainty interval width (0.8 → 10th/90th percentile).
        """
        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_mode        = seasonality_mode
        self.weekly_seasonality      = weekly_seasonality
        self.yearly_seasonality      = yearly_seasonality
        self.interval_width          = interval_width

    def _build_model(self):
        """Instantiate and configure a Prophet model."""
        Prophet = _import_prophet()
        return Prophet(
            changepoint_prior_scale=self.changepoint_prior_scale,
            seasonality_mode=self.seasonality_mode,
            weekly_seasonality=self.weekly_seasonality,
            yearly_seasonality=self.yearly_seasonality,
            interval_width=self.interval_width,
            # Clamp forecast to [0, 10] using logistic growth
            # (HNDL score is bounded)
            growth="linear",
        )

    def forecast(
        self,
        history:       list[dict[str, Any]],
        horizon_years: int = 5,
    ) -> list[ForecastBand]:
        """
        Run Prophet on historical HNDL data and return P10/P50/P90 forecast bands.

        Args:
            history:       Time series as list of {"ds": "YYYY-MM-DD", "y": float}.
                           Minimum 2 data points required; Prophet works best with ≥ 30.
            horizon_years: Number of years to forecast ahead.

        Returns:
            List of ForecastBand objects (one per forecasted period, quarterly).
        """
        if len(history) < 2:
            logger.warning("prophet_insufficient_data", n=len(history))
            return self._synthetic_fallback(horizon_years)

        df = pd.DataFrame(history)
        df["ds"] = pd.to_datetime(df["ds"])
        df["y"]  = pd.to_numeric(df["y"], errors="coerce").fillna(5.0)
        df = df.dropna(subset=["ds", "y"]).sort_values("ds").reset_index(drop=True)

        # Cap HNDL to [0, 10] to prevent unrealistic extrapolation
        df["y"] = df["y"].clip(0.0, 10.0)

        model = self._build_model()

        import logging
        logging.getLogger("prophet").setLevel(logging.WARNING)
        logging.getLogger("cmdstanpy").setLevel(logging.WARNING)

        model.fit(df)

        # Generate future quarterly dates
        horizon_days = horizon_years * 365
        future = model.make_future_dataframe(periods=horizon_days // 90, freq="QS")
        forecast_df = model.predict(future)

        # Filter to future-only rows
        last_historic = df["ds"].max()
        future_mask   = forecast_df["ds"] > last_historic
        forecast_df   = forecast_df[future_mask].copy()

        bands: list[ForecastBand] = []
        for _, row in forecast_df.iterrows():
            bands.append(ForecastBand(
                date=row["ds"].strftime("%Y-%m-%d"),
                p10=round(max(0.0, float(row.get("yhat_lower", row["yhat"]))), 3),
                p50=round(max(0.0, float(row["yhat"])), 3),
                p90=round(min(10.0, float(row.get("yhat_upper", row["yhat"]))), 3),
            ))

        logger.info(
            "prophet_forecast_complete",
            data_points=len(df),
            horizon_years=horizon_years,
            forecast_periods=len(bands),
        )
        return bands

    def _synthetic_fallback(self, horizon_years: int) -> list[ForecastBand]:
        """Return linearly-increasing bands when insufficient historical data exists."""
        bands = []
        today = datetime.utcnow()
        for q in range(horizon_years * 4):
            future_date = today + timedelta(days=q * 90)
            growth      = min(10.0, 5.0 + q * 0.15)    # simple linear proxy
            bands.append(ForecastBand(
                date=future_date.strftime("%Y-%m-%d"),
                p10=round(max(0.0, growth - 1.0), 3),
                p50=round(growth, 3),
                p90=round(min(10.0, growth + 1.5), 3),
            ))
        return bands

    @staticmethod
    def trend_direction(bands: list[ForecastBand]) -> str:
        """Classify the overall forecast trend from the P50 series."""
        if len(bands) < 2:
            return "stable"
        first = bands[0].p50
        last  = bands[-1].p50
        delta = last - first
        if delta >  0.5:
            return "increasing"
        elif delta < -0.5:
            return "decreasing"
        return "stable"


# ─────────────────────────────────────────────────────────────────────────────
# Monte Carlo Simulation
# ─────────────────────────────────────────────────────────────────────────────

class MonteCarloCRQCSimulator:
    """
    Monte Carlo simulation of CRQC arrival year and migration race outcome.

    Models uncertainty in:
      • Quantum hardware progress        → CRQC arrival year distribution
      • Organisational migration speed   → Migration velocity distribution
      • Adversarial harvest window       → How long encrypted data can be stored

    10,000 simulation runs produce P10/P50/P90 exposure year bands and
    conditional breach probability estimates.

    Usage::

        mc = MonteCarloCRQCSimulator()
        summary = mc.run(t_migrate_mean=4.5)
    """

    def __init__(
        self,
        n_simulations: int = N_MC_RUNS,
        seed:          int = RNG_SEED,
    ) -> None:
        self.n_simulations = n_simulations
        self.seed          = seed
        self._rng          = np.random.default_rng(seed)

    def run(
        self,
        t_migrate_mean: float = MIGRATE_MEAN,
        t_migrate_std:  float = MIGRATE_STD,
        crqc_min:       float = CRQC_MIN,
        crqc_mode:      float = CRQC_MODE,
        crqc_max:       float = CRQC_MAX,
    ) -> MonteCarloSummary:
        """
        Run N Monte Carlo simulations and compute HNDL exposure statistics.

        Simulation model (per run):
            1. Sample quantum_arrival_year ~ Triangular(crqc_min, crqc_mode, crqc_max)
            2. Sample harvest_window_years ~ Uniform(HARVEST_MIN, HARVEST_MAX)
            3. Sample t_migrate ~ Normal(t_migrate_mean, t_migrate_std), clamped > 0
            4. t_harvest = current_year + harvest_window_years
            5. t_decrypt = quantum_arrival_year - current_year  (years until CRQC)
            6. BREACH = 1  iff  t_harvest + t_decrypt  <  t_migrate

        When breach occurs, the "exposure year" = quantum_arrival_year (the year
        the adversary can start decrypting harvested data).

        Args:
            t_migrate_mean: Mean migration duration in years (asset-specific).
            t_migrate_std:  Std-dev of migration duration.
            crqc_min/mode/max: Triangular distribution params for CRQC arrival.

        Returns:
            MonteCarloSummary with P10/P50/P90 breach years and conditional probs.
        """
        rng = self._rng

        # ── Sample all random variables at once (vectorised) ────────────────
        quantum_arrival = rng.triangular(crqc_min, crqc_mode, crqc_max, size=self.n_simulations)
        harvest_window  = rng.uniform(HARVEST_MIN, HARVEST_MAX, size=self.n_simulations)
        t_migrate       = np.clip(
            rng.normal(t_migrate_mean, t_migrate_std, size=self.n_simulations),
            0.5, 20.0,
        )

        # ── MOSCA evaluation ─────────────────────────────────────────────────
        t_harvest = harvest_window               # years of already-captured data
        t_decrypt = np.maximum(0.0, quantum_arrival - _CURRENT_YEAR)   # years until CRQC breaks it

        breach_mask     = (t_harvest + t_decrypt) < t_migrate          # True = at risk
        breach_years    = quantum_arrival[breach_mask]

        if len(breach_years) == 0:
            # No breach scenarios → return safe profile
            logger.info("monte_carlo_no_breaches", runs=self.n_simulations)
            return MonteCarloSummary(
                n_simulations=self.n_simulations,
                median_exposure_year=float(crqc_max),
                p10_exposure_year=float(crqc_max),
                p90_exposure_year=float(crqc_max),
                prob_breach_before_2030=0.0,
                prob_breach_before_2035=0.0,
            )

        p10_year = float(np.percentile(breach_years, 10))
        p50_year = float(np.percentile(breach_years, 50))
        p90_year = float(np.percentile(breach_years, 90))

        # Conditional breach probabilities
        prob_before_2030 = float(np.mean(breach_years <= 2030))
        prob_before_2035 = float(np.mean(breach_years <= 2035))

        summary = MonteCarloSummary(
            n_simulations=self.n_simulations,
            median_exposure_year=round(p50_year, 1),
            p10_exposure_year=round(p10_year, 1),
            p90_exposure_year=round(p90_year, 1),
            prob_breach_before_2030=round(prob_before_2030, 4),
            prob_breach_before_2035=round(prob_before_2035, 4),
        )

        breach_pct = 100 * len(breach_years) / self.n_simulations
        logger.info(
            "monte_carlo_complete",
            n=self.n_simulations,
            breach_pct=round(breach_pct, 2),
            p50_year=round(p50_year, 1),
            prob_2030=round(prob_before_2030, 4),
        )
        return summary


# ─────────────────────────────────────────────────────────────────────────────
# Combined Forecasting Service
# ─────────────────────────────────────────────────────────────────────────────

class HNDLForecastingService:
    """
    Unified façade combining Prophet time-series and Monte Carlo simulation.

    Returns a ForecastResult suitable for direct API serialisation.

    Usage::

        svc = HNDLForecastingService()
        result = svc.run(
            asset_ids=["uuid1", "uuid2"],
            history=[{"ds": "2025-01-01", "y": 6.2}, ...],
            t_migrate_mean=4.5,
            horizon_years=5,
        )
    """

    def __init__(
        self,
        prophet_kwargs: dict[str, Any] | None = None,
        mc_n_simulations: int = N_MC_RUNS,
    ) -> None:
        self.prophet   = HNDLProphetForecaster(**(prophet_kwargs or {}))
        self.mc        = MonteCarloCRQCSimulator(n_simulations=mc_n_simulations)

    def run(
        self,
        asset_ids:      list[str],
        history:        list[dict[str, Any]],
        t_migrate_mean: float = MIGRATE_MEAN,
        t_migrate_std:  float = MIGRATE_STD,
        horizon_years:  int   = 5,
    ) -> ForecastResult:
        """
        Run both forecast methods and combine into a ForecastResult.

        Args:
            asset_ids:      UUIDs of assets this forecast applies to.
            history:        Time-series data [{"ds": "YYYY-MM-DD", "y": float}, …].
            t_migrate_mean: Mean migration duration (years) — from HNDLScorer / org profile.
            t_migrate_std:  Std-dev of migration duration.
            horizon_years:  Prophet forecast horizon in years.

        Returns:
            ForecastResult with all bands and summary statistics.
        """
        logger.info("forecasting_start", assets=len(asset_ids), horizon=horizon_years)

        prophet_bands = self.prophet.forecast(history, horizon_years=horizon_years)
        trend         = self.prophet.trend_direction(prophet_bands)
        mc_summary    = self.mc.run(
            t_migrate_mean=t_migrate_mean,
            t_migrate_std=t_migrate_std,
        )

        result = ForecastResult(
            asset_ids=asset_ids,
            forecast_horizon_years=horizon_years,
            prophet_forecast=prophet_bands,
            monte_carlo=mc_summary,
            trend_direction=trend,
        )

        logger.info(
            "forecasting_complete",
            trend=trend,
            p50_breach=mc_summary.median_exposure_year,
            prob_2030=mc_summary.prob_breach_before_2030,
        )
        return result
