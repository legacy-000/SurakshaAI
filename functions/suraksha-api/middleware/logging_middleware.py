import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from utilities.logger import SystemLogger

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that intercept incoming HTTP requests, assigns trace IDs, and records durations.
    """
    async def dispatch(self, request: Request, call_next):
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        SystemLogger.info(
            f"Method: {request.method} Path: {request.url.path} "
            f"Status: {response.status_code} Duration: {duration:.4f}s - Trace: {trace_id}"
        )
        
        response.headers["X-Trace-ID"] = trace_id
        return response
