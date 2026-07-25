"""Catalyst Advanced I/O Function entry point for Crime Intelligence Platform.

Catalyst's Python runtime calls ``handler(request)`` with a Flask Request and
expects a Flask Response back.
"""
import sys
import os
import json
import traceback

from flask import Response

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Catalyst's console exposes no env-variable UI for functions and its zip
# upload ignores deployment.env_variables, so credentials ship in the bundle.
# Loaded by absolute path (not pydantic's env_file, which is CWD-relative)
# and before app.config is imported, so Settings picks them up normally.
_envfile = os.path.join(_root, ".env")
if os.path.isfile(_envfile):
    with open(_envfile, encoding="utf-8") as _fh:
        for _line in _fh:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

os.environ.setdefault("USE_CATALYST", "true")
os.environ.setdefault("LLM_PROVIDER", "mock")

# Catalyst serves the uploaded bundle as-is and never pip-installs
# requirements.txt, so third-party deps ship pre-vendored alongside it.
_vendor = os.path.join(_root, "vendor")
if os.path.isdir(_vendor) and _vendor not in sys.path:
    sys.path.insert(1, _vendor)

_adapter = None
_init_error = None
_init_stage = "not started"

try:
    _init_stage = "importing app.config"
    from app.config import settings  # noqa: F401

    _init_stage = "importing app.main.create_app"
    from app.main import create_app

    _init_stage = "importing catalyst_adapter"
    from catalyst_adapter import CatalystASGIAdapter

    _init_stage = "creating FastAPI app"
    _app = create_app()

    # FastAPI's lifespan never runs here (we drive the ASGI app per request),
    # so the Catalyst datastore client has to be initialised by hand.
    _init_stage = "initialising catalyst store"
    from app.catalyst_store import init_catalyst_store
    init_catalyst_store()

    _init_stage = "creating ASGI adapter"
    _adapter = CatalystASGIAdapter(_app, strip_prefix="/server/suraksha_api")

    _init_stage = "ready"
except Exception:
    _init_error = traceback.format_exc()


def handler(request):
    # Stash the Catalyst headers so SDK calls work from FastAPI's threadpool
    # workers, where the SDK's own thread-local would be empty.
    try:
        from app.catalyst_ctx import set_headers
        set_headers(request.headers)
    except Exception:
        pass

    if _init_error:
        return Response(
            json.dumps({"error": "Function init failed",
                        "stage": _init_stage,
                        "traceback": _init_error,
                        "python": sys.version}),
            status=500, content_type="application/json")
    return _adapter.handle(request)
