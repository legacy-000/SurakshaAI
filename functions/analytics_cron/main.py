"""Catalyst cron function: precomputes heavy analytics (Part B).

Runs on the 15-minute cron budget (Part A). Persists snapshots to Data Store
via :class:`CatalystRowPrecomputedStore`. The Advanced I/O serve-side
reads them via the same store with a single SELECT - keeping the chat
path inside the 30-s ceiling (Part A.1).

Each phase runs in a try/except so a single-phase failure does not
abort the rest of the run. The handler always returns a JSON-shaped
dict so the cron event is observable in Catalyst logs.
"""
import logging
import os
import sys
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
_COMMON = os.path.abspath(os.path.join(_HERE, os.pardir, "suraksha_ai", "common"))
sys.path.insert(0, _COMMON)

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(name)s] %(levelname)s %(message)s")


# Tables that must exist before the cron can write precomputed snapshots.
# These are created once at project setup via the Catalyst console; the
# cron guards against silent missing-table writes with a noisy pre-flight.
PRECOMPUTED_TABLES = (
    "TrendSnapshot", "HotspotSnapshot",
    "ForecastResult", "ResolvedEntity", "IPSScore",
)


def _safe(name, fn):
    try:
        out = fn()
        logger.info("phase ok: %s -> %s", name, out)
        return ("ok", out)
    except Exception as exc:
        logger.error("phase failed: %s :: %s\n%s", name, exc, traceback.format_exc())
        return ("error", str(exc))


def _preflight_tables(app) -> dict:
    """Verify the 5 precomputed-result tables exist in Data Store.

    Returns a dict with the missing/present table lists; if any are
    missing, the cron is aborted to avoid silently losing precompute
    data. Bootstrap instructions are in the deploy doc.
    """
    try:
        ds = app.datastore()
        # Catalyst SDK exposes a TableListController for listing tables.
        existing = {t.table_name for t in ds.table().get_all_tables()}
    except Exception as exc:
        # If the platform API is unreachable, fail loud rather than
        # silently skipping the write.
        logger.error("preflight: cannot list tables: %s", exc)
        return {"checked": False, "error": str(exc)}

    missing = [t for t in PRECOMPUTED_TABLES if t not in existing]
    if missing:
        logger.warning(
            "preflight: %d missing tables: %s. "
            "Create them in Catalyst console (Data Store > Tables) with "
            "columns (SnapshotKey:String, Payload:Clob, UpdatedAt:DateTime).",
            len(missing), missing,
        )
        return {"checked": True, "missing": missing}
    return {"checked": True, "missing": []}


def handler(event, context):
    """Catalyst cron entry point.

    Composition: instantiate the analyzers with the repository + store wired
    once at start; call :func:`compute_all_and_store` on each in a single
    try/except envelope per phase.
    """
    try:
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize()
    except Exception as exc:
        logger.error("catalyst init failed; aborting run: %s", exc)
        _safe_close(context)
        return {"status": "error", "reason": "init_failed", "detail": str(exc)}

    preflight = _preflight_tables(app)
    if preflight.get("missing"):
        _safe_close(context)
        return {
            "status": "error",
            "reason": "missing_tables",
            "missing": preflight["missing"],
            "fix": "Create the listed tables in the Catalyst console with "
                   "columns (SnapshotKey:String, Payload:Clob, UpdatedAt:DateTime) "
                   "then re-run the cron.",
        }

    from common.analytics.trend_analyzer import TrendAnalyzer
    from common.analytics.hotspot_detector import HotspotDetector
    from common.forecast.forecaster import build_forecaster
    from common.offender.entity_resolver import build_entity_resolver

    results = {}
    for name, build in (
        ("trends", lambda: TrendAnalyzer().compute_all_and_store(app)),
        ("hotspots", lambda: HotspotDetector().compute_all_and_store(app)),
        ("forecast", lambda: build_forecaster().compute_all_and_store(app)),
        ("entity_resolution", lambda: build_entity_resolver().compute_all_and_store(app)),
    ):
        results[name] = _safe(name, build)

    logger.info("analytics_cron run complete: %s", {k: v[0] for k, v in results.items()})
    _safe_close(context)
    return {"status": "ok", "phases": {k: v[0] for k, v in results.items()},
            "summary": {k: v[1] for k, v in results.items()}}


def _safe_close(context):
    try:
        context.close()
    except Exception:
        pass
