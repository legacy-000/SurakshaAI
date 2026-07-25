"""Carries the Catalyst request headers across threads for zcatalyst_sdk.

zcatalyst_sdk.initialize() reads the Catalyst headers from a thread-local that
is only populated by handing it the request. The function handler runs on the
main thread, but FastAPI dispatches sync endpoints to a threadpool worker, so
the thread-local is empty by the time app code calls the SDK.

The handler stashes the headers here; app code calls init_sdk(), which re-seeds
the SDK on whatever thread it happens to be running on.

ponytail: module-level global assumes one in-flight request per function
instance, which holds for Catalyst's serverless model. If a runtime ever runs
requests concurrently in one container, swap this for a contextvar.
"""
from __future__ import annotations

_headers: dict = {}


class _Req:
    """Minimal stand-in — the SDK only reads `.headers`."""

    def __init__(self, headers):
        self.headers = headers


def set_headers(headers) -> None:
    global _headers
    _headers = dict(headers or {})


def get_headers() -> dict:
    return _headers


def init_sdk():
    """Initialise zcatalyst_sdk on the current thread. Raises on failure."""
    import zcatalyst_sdk
    if _headers:
        return zcatalyst_sdk.initialize(req=_Req(_headers))
    return zcatalyst_sdk.initialize()
