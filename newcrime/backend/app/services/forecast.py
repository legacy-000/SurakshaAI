"""QuickML Prophet integration for crime forecasting.

QuickML exposes one generic call — predict(endpoint_key, input_data) — against
a *published endpoint*, not a model id. There is no app.quickml() and no
model() accessor; earlier code called both and failed silently into an empty
forecast.
"""
from __future__ import annotations

from ..config import settings

# Last failure, surfaced by /api/health. A forecast that silently returns []
# is indistinguishable from one that legitimately has nothing to predict.
last_error: str | None = None


def _predict(input_data: dict):
    global last_error
    if not settings.quickml_endpoint_key:
        last_error = "QUICKML_ENDPOINT_KEY not set"
        return None
    try:
        from ..catalyst_ctx import init_sdk
        result = init_sdk().quick_ml().predict(
            settings.quickml_endpoint_key, input_data)
        last_error = None
        return result
    except Exception as e:
        last_error = f"{type(e).__name__}: {e}"[:300]
        return None


def _rows(result) -> list[dict]:
    """Normalise whatever shape the endpoint returns into forecast rows."""
    if isinstance(result, dict):
        for key in ("predictions", "forecast", "data", "result", "output"):
            if isinstance(result.get(key), list):
                result = result[key]
                break
    if not isinstance(result, list):
        return []
    out = []
    for row in result:
        if not isinstance(row, dict):
            continue
        date = row.get("ds") or row.get("date")
        value = row.get("yhat", row.get("predicted_count"))
        if date is None or value is None:
            continue
        out.append({
            "date": str(date)[:10],
            "predicted_count": float(value),
            "lower_bound": float(row.get("yhat_lower", row.get("lower_bound", value))),
            "upper_bound": float(row.get("yhat_upper", row.get("upper_bound", value))),
        })
    return out


def get_forecast(crime_type: str | None = None, district: str | None = None,
                 horizon_days: int = 30) -> list[dict]:
    payload: dict = {"horizon": horizon_days}
    if crime_type:
        payload["crime_type"] = crime_type
    if district:
        payload["district"] = district
    result = _predict(payload)
    return _rows(result) if result is not None else []


def get_risk_assessment(district: str) -> dict:
    """Forecast the main crime types for one district.

    One network round trip per crime type inside a serverless request, so keep
    the list short.
    """
    from ..services.nlq import CRIME_LEXICON
    risks = []
    for crime_type in sorted(set(CRIME_LEXICON.values()))[:8]:
        forecast = get_forecast(crime_type=crime_type, district=district)
        if not forecast:
            continue
        total = sum(f["predicted_count"] for f in forecast)
        risks.append({
            "crime_type": crime_type,
            "predicted_cases": round(total, 1),
            "risk_level": "High" if total > 10 else "Medium" if total > 3 else "Low",
        })
    risks.sort(key=lambda r: -r["predicted_cases"])
    return {
        "district": district,
        "horizon_days": 30,
        "risks": risks,
        "overall_risk": ("High" if any(r["risk_level"] == "High" for r in risks)
                         else "Medium" if risks else "Unknown"),
        "error": last_error,
    }
