"""Forecaster closed-for-modification, open-for-extension (Part E.2/E.3).

Cache import-availability of optional ML libs at module load. Strategies are
interchangeable — every implementation returns the same shape from
``forecast()`` so callers never branch on the concrete algorithm
(Liskov compliance).

Wiring lives in :func:`build_forecaster`. Adding a new method = add a new
strategy class + register it in the factory. The Forecaster class itself
must never change to pick a different algorithm.
"""
from __future__ import annotations

import math
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Iterable, Optional

from models.dto import ForecastRequestDTO, ForecastResultDTO, ForecastDataPoint, EvidenceReferenceDTO

try:
    from prophet import Prophet as _Prophet  # type: ignore
except ImportError:
    _Prophet = None  # only available inside analytics_cron requirements

try:
    from statsmodels.tsa.arima.model import ARIMA as _ARIMA  # type: ignore
except ImportError:
    _ARIMA = None


def _seasonal_naive_pred(train: list[float], horizon: int, drift: float) -> list[float]:
    preds: list[float] = []
    for i in range(horizon):
        if i < 7 and len(train) >= 7:
            seasonal = train[-(7 - i)]
        elif i >= 7:
            seasonal = preds[i - 7]
        else:
            seasonal = train[-1] if train else 0.0
        preds.append(max(0.0, round(seasonal + drift, 1)))
    return preds


class ForecastStrategy(ABC):
    """Single contract for every algorithm.

    LSP: every implementation returns ``{points, residual_std, model_name}``
    where ``points`` is a list of ``ForecastDataPoint`` instances. The caller
    never inspects the algorithm — only consumes that shape.
    """

    name: str = "ForecastStrategy"

    @abstractmethod
    def forecast(self, series: list[float], horizon: int) -> dict:
        """Synchronous forecast. ``series`` is daily observation values."""

    @staticmethod
    def _empty(horizon: int, model_name: str) -> dict:
        return {
            "points": [],
            "residual_std": 0.0,
            "model_name": model_name,
            "horizon": horizon,
        }


class SeasonalNaiveStrategy(ForecastStrategy):
    """Always-available fallback. No external deps."""

    name = "SeasonalNaive v1"

    def forecast(self, series: list[float], horizon: int) -> dict:
        if not series:
            return self._empty(horizon, self.name)
        horizon = max(horizon, 1)
        drift = (series[-1] - series[0]) / len(series) if len(series) > 1 else 0.0
        full_series = list(series)
        preds = _seasonal_naive_pred(full_series, horizon, drift)
        # Residual std is unknown without a holdout split; approximate with
        # recent-window dispersion so confidence intervals are still useful.
        recent = series[-14:] if len(series) >= 14 else series
        mean = sum(recent) / len(recent) if recent else 0.0
        var = sum((x - mean) ** 2 for x in recent) / len(recent) if recent else 0.0
        resid_std = math.sqrt(var)
        now = datetime.now()
        points = [
            ForecastDataPoint(
                date=(now + timedelta(days=i + 1)).strftime("%Y-%m-%d"),
                predicted=p,
                lower=max(0.0, round(p - 1.96 * resid_std, 1)),
                upper=round(p + 1.96 * resid_std, 1),
            )
            for i, p in enumerate(preds)
        ]
        return {"points": points, "residual_std": resid_std, "model_name": self.name, "horizon": horizon}


class ARIMAForecastStrategy(ForecastStrategy):
    """Optional — depends on statsmodels (analytics_cron)."""

    name = "ARIMA(1,0,1)"

    def forecast(self, series: list[float], horizon: int) -> dict:
        if _ARIMA is None or len(series) < 30:
            return SeasonalNaiveStrategy().forecast(series, horizon)
        try:
            fitted = _ARIMA(series, order=(1, 0, 1)).fit()
            fc = fitted.forecast(steps=horizon)
            preds = [max(0.0, float(v)) for v in fc]
            resid_std = float(fitted.resid.std()) if hasattr(fitted, "resid") else 0.0
        except Exception:
            return SeasonalNaiveStrategy().forecast(series, horizon)
        now = datetime.now()
        points = [
            ForecastDataPoint(
                date=(now + timedelta(days=i + 1)).strftime("%Y-%m-%d"),
                predicted=round(p, 1),
                lower=max(0.0, round(p - 1.96 * resid_std, 1)),
                upper=round(p + 1.96 * resid_std, 1),
            )
            for i, p in enumerate(preds)
        ]
        return {"points": points, "residual_std": resid_std, "model_name": self.name, "horizon": horizon}


class ProphetForecastStrategy(ForecastStrategy):
    """Optional — depends on prophet (analytics_cron only)."""

    name = "Prophet"

    def forecast(self, series: list[float], horizon: int) -> dict:
        if _Prophet is None or len(series) < 30:
            return SeasonalNaiveStrategy().forecast(series, horizon)
        try:
            base = datetime.now() - timedelta(days=len(series))
            df = {"ds": [(base + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(len(series))],
                  "y": [float(v) for v in series]}
            m = _Prophet(daily_seasonality=False, weekly_seasonality=True)
            m.fit(df)
            future = m.make_future_dataframe(periods=horizon)
            out = m.predict(future).tail(horizon)
            preds = [max(0.0, float(y)) for y in out["yhat"]]
            resid_std = float((df["y"][-horizon:] - preds).std()) if horizon <= len(series) else 0.0
        except Exception:
            return SeasonalNaiveStrategy().forecast(series, horizon)
        now = datetime.now()
        points = [
            ForecastDataPoint(
                date=(now + timedelta(days=i + 1)).strftime("%Y-%m-%d"),
                predicted=round(float(p), 1),
                lower=max(0.0, round(float(out["yhat_lower"].iloc[i]), 1)),
                upper=round(float(out["yhat_upper"].iloc[i]), 1),
            )
            for i, p in enumerate(preds)
        ]
        return {"points": points, "residual_std": resid_std, "model_name": self.name, "horizon": horizon}


def build_forecaster(store=None) -> "Forecaster":
    """Composition root for the forecaster. Tries fancy first, falls back.

    Adding a new strategy = add its class above + add a branch here. Never
    edit ``Forecaster`` itself — that is the protected boundary (Part E.2).
    """
    if _Prophet is not None:
        strategy: ForecastStrategy = ProphetForecastStrategy()
    elif _ARIMA is not None:
        strategy = ARIMAForecastStrategy()
    else:
        strategy = SeasonalNaiveStrategy()
    return Forecaster(strategy, store=store)


class Forecaster:
    """Closed for modification (Part E.2), delegates work to a strategy."""

    def __init__(self, strategy: ForecastStrategy, store=None):
        self.strategy = strategy
        self._store = store

    @property
    def strategy_name(self) -> str:
        return self.strategy.name

    def forecast_series(self, series: list[float], horizon: int = 30) -> dict:
        return self.strategy.forecast(series, horizon)

    def compute_all_and_store(self, catalyst_app) -> dict:
        """Cron path (Part B). Enumerates districts and writes forecasts."""
        from common.db.datastore_client import DatastoreClient
        from common.repositories.zcql_impl import CatalystRowPrecomputedStore
        db = DatastoreClient(catalyst_app)
        store = self._store or CatalystRowPrecomputedStore(db)
        districts = self._all_district_ids(db)
        if not districts:
            return {"status": "skipped", "reason": "no districts"}
        sub_head_ids = [1]  # one canonical sub-head keeps the cron under 15-min budget
        count = 0
        for did in districts[:50]:
            for shid in sub_head_ids:
                req = ForecastRequestDTO(
                    district_id=did, crime_sub_head_id=shid,
                    forecast_horizon_days=30, training_window_days=365
                )
                res = self.forecast(req, db=db)
                store.save_forecast(did, shid, res.model_dump())
                count += 1
        return {"status": "ok", "forecasts": count}

    @staticmethod
    def _all_district_ids(db) -> list[int]:
        if not getattr(db, "is_connected", False):
            return []
        res = db.execute_non_query("SELECT DistrictID FROM District LIMIT 300")
        if "error" in res or not res.get("rows"):
            return []
        cols = res.get("columns", [])
        if "DistrictID" not in cols:
            return []
        idx = cols.index("DistrictID")
        out: list[int] = []
        for row in res["rows"]:
            try:
                out.append(int(row[idx]))
            except (TypeError, ValueError, IndexError):
                pass
        return out

    def forecast(self, req: ForecastRequestDTO, db=None) -> ForecastResultDTO:
        run_id = str(uuid.uuid4())
        horizon = req.forecast_horizon_days
        if db is None:
            raise RuntimeError("forecast: no DB connection provided")
        daily_counts = self._fetch_training_data(req, db)
        if daily_counts is None or len(daily_counts) < 14:
            raise RuntimeError(f"forecast: insufficient training data ({len(daily_counts) if daily_counts else 0} days, need 14)")
        result = self.strategy.forecast(daily_counts, horizon)
        return ForecastResultDTO(
            run_id=run_id,
            model=result["model_name"],
            district=f"District_{req.district_id}",
            crime_type=f"CrimeType_{req.crime_sub_head_id}",
            training_days=len(daily_counts),
            horizon_days=horizon,
            metrics={"mae": 0.0, "rmse": 0.0, "baseline_mae": 0.0, "mape": None},
            forecast=result["points"],
            evidence_refs=[EvidenceReferenceDTO(
                evidence_id=f"ev_fc_{run_id[:8]}",
                evidence_type="computed_statistic",
                source_table="CaseMaster",
                source_record_count=len(daily_counts),
                filter_summary=f"Forecast training window: {req.training_window_days}d",
                display_label=f"Forecast based on {len(daily_counts)} days of training data",
            )],
        )

    # Keeps the original DB-driven data fetch for backward compatibility.
    # The repository abstractions built under Part E.5 can replace this in a
    # follow-up; for now, the Forecaster keeps its existing contract alive.
    def _fetch_training_data(self, req: ForecastRequestDTO, db) -> Optional[list[float]]:
        if db is None or not getattr(db, "is_connected", False):
            return None
        try:
            unit_res = db.execute_non_query(
                f"SELECT UnitID FROM Unit WHERE DistrictID = {int(req.district_id)} LIMIT 300"
            )
        except Exception:
            return None
        if "error" in unit_res or unit_res.get("row_count", 0) == 0:
            return None
        unit_cols = unit_res.get("columns", [])
        unit_idx = unit_cols.index("UnitID") if "UnitID" in unit_cols else 0
        station_ids: list[int] = []
        for row in unit_res.get("rows", []):
            try:
                station_ids.append(int(row[unit_idx]))
            except (TypeError, ValueError, IndexError):
                pass
        if not station_ids:
            return None
        start = (datetime.now() - timedelta(days=req.training_window_days)).strftime("%Y-%m-%d")
        try:
            sql = (
                f"SELECT CrimeRegisteredDate, ROWID FROM CaseMaster "
                f"WHERE PoliceStationID IN ({', '.join(str(i) for i in station_ids)}) "
                f"AND CrimeMinorHeadID = {int(req.crime_sub_head_id)} "
                f"AND CrimeRegisteredDate >= '{start}'"
            )
            res = db.execute_non_query(sql)
        except Exception:
            return None
        if "error" in res or res.get("row_count", 0) == 0:
            return None
        cols = res["columns"]
        date_idx = cols.index("CrimeRegisteredDate") if "CrimeRegisteredDate" in cols else 0
        daily: dict[str, int] = {}
        for row in res["rows"]:
            ds = row[date_idx] if date_idx < len(row) else None
            if ds:
                key = str(ds)[:10]
                daily[key] = daily.get(key, 0) + 1
        sorted_dates = sorted(daily.keys())
        return [daily[d] for d in sorted_dates]
