"""Forecaster public surface (Part E.2 / Part H wiring).

Re-exports :func:`build_forecaster` and the ``ForecastStrategy`` family so
callers can ``from common.forecast import build_forecaster`` rather than
reaching into the implementation module. Adding a new strategy does NOT
require editing this file — only :mod:`common.forecast.forecaster` does.

Composition-root contract remains:
    forecaster = build_forecaster()        -> uses best available strategy
    forecaster.forecast_series(series, h)  -> runs configured strategy
"""
from common.forecast.forecaster import (
    Forecaster,
    ForecastStrategy,
    SeasonalNaiveStrategy,
    ARIMAForecastStrategy,
    ProphetForecastStrategy,
    build_forecaster,
)

__all__ = [
    "Forecaster",
    "ForecastStrategy",
    "SeasonalNaiveStrategy",
    "ARIMAForecastStrategy",
    "ProphetForecastStrategy",
    "build_forecaster",
]
