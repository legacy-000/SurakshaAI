import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_backend_root = str(Path(__file__).parent.resolve())
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from routes import api_router
from utilities.logger import SystemLogger

app = FastAPI(
    title="SURAKSHA AI - Backend Core",
    description="Crime Intelligence Platform for Karnataka Police",
    version="0.1.0",
)

allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,https://suraksha-frontend-pbdnbciy.onslate.in")
origins = [origin.strip() for origin in allowed_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def health_check():
    SystemLogger.info("Root health check request received.")
    return {
        "service": "SURAKSHA AI Backend",
        "status": "Running",
        "platform": "Zoho Catalyst Serverless"
    }


# Catalyst Advanced I/O handler
from flask import Request as FlaskRequest, Response as FlaskResponse
from asgiref.sync import async_to_sync
from urllib.parse import unquote


def handler(request: FlaskRequest):
    """Catalyst Advanced I/O entry point."""
    from starlette.datastructures import Headers, QueryParams
    from starlette.requests import Request as StarletteRequest

    body = request.get_data()

    async def get_body():
        return body

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": request.method,
        "scheme": request.scheme,
        "path": unquote(request.path),
        "raw_path": unquote(request.path).encode(),
        "query_string": request.query_string,
        "root_path": "",
        "headers": [(k.lower().encode(), v.encode()) for k, v in request.headers.items()],
        "client": ("127.0.0.1", 0),
        "server": (request.host.split(":")[0], 80),
    }

    # Track lifespan init
    if not hasattr(app.state, "_lifespan_done"):
        ls_scope = {"type": "lifespan", "asgi": {"version": "3.0", "spec_version": "2.3"}}

        async def _lifespan():
            receive_called = False
            async def receive():
                nonlocal receive_called
                if not receive_called:
                    receive_called = True
                    return {"type": "lifespan.startup"}
                return {"type": "lifespan.shutdown"}
            async def send(msg):
                pass
            await app(ls_scope, receive, send)

        async_to_sync(_lifespan)()
        app.state._lifespan_done = True

    response_status = 200
    response_headers = []
    response_body = b""
    send_complete = False

    async def receive():
        nonlocal send_complete
        if not send_complete:
            send_complete = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        nonlocal response_status, response_headers, response_body
        if message["type"] == "http.response.start":
            response_status = message["status"]
            response_headers = message.get("headers", [])
        elif message["type"] == "http.response.body":
            response_body = message.get("body", b"")

    async_to_sync(lambda: app(scope, receive, send))()

    return FlaskResponse(
        response=response_body,
        status=response_status,
        headers=[(k.decode(), v.decode()) for k, v in response_headers
                 if k.decode().lower() not in ("content-length",)],
    )


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    SystemLogger.info(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
