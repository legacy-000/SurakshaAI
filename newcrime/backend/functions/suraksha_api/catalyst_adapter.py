"""ASGI <-> Catalyst request/response bridge.

Catalyst's Python Advanced I/O runtime hands the handler a Flask ``Request``
and expects a Flask ``Response`` back, so this drives the existing FastAPI
ASGI app once per request and repackages the result.
"""
from __future__ import annotations

import asyncio

from flask import Response


class CatalystASGIAdapter:
    def __init__(self, asgi_app, strip_prefix: str = ""):
        self._app = asgi_app
        self._strip_prefix = strip_prefix.rstrip("/")

    def handle(self, request) -> Response:
        loop = asyncio.new_event_loop()
        try:
            status, headers, body = loop.run_until_complete(self._dispatch(request))
        finally:
            loop.close()
        return Response(body, status=status, headers=headers)

    async def _dispatch(self, request):
        scope = self._to_asgi_scope(request)
        body_bytes = request.get_data() or b""

        status_code = 200
        response_headers: list[tuple[str, str]] = []
        body_parts: list[bytes] = []

        async def receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        async def send(event):
            nonlocal status_code, response_headers
            if event["type"] == "http.response.start":
                status_code = event["status"]
                response_headers = [
                    (k.decode() if isinstance(k, bytes) else k,
                     v.decode() if isinstance(v, bytes) else v)
                    for k, v in event.get("headers", [])
                ]
            elif event["type"] == "http.response.body":
                body_parts.append(event.get("body", b""))

        await self._app(scope, receive, send)
        return status_code, response_headers, b"".join(body_parts)

    def _to_asgi_scope(self, request) -> dict:
        path = request.path or "/"
        if self._strip_prefix and path.startswith(self._strip_prefix):
            path = path[len(self._strip_prefix):] or "/"

        return {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": request.method.upper(),
            "path": path,
            "raw_path": path.encode("utf-8"),
            "root_path": "",
            "scheme": request.scheme or "https",
            "query_string": request.query_string or b"",
            "headers": [(k.lower().encode("latin-1"), v.encode("latin-1"))
                        for k, v in request.headers.items()],
            "client": (request.remote_addr or "127.0.0.1", 0),
            "server": (request.host.split(":")[0] if request.host else "localhost", 443),
        }
