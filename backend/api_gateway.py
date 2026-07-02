"""
Catalyst API Gateway handler for SurakshaAI.
Replaces traditional API Gateway with Catalyst-native routing logic.
Routes incoming /api/* requests to the appropriate backend controller.
"""
from typing import Dict, Any
from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.controllers.auth_controller import AuthController
from backend.controllers.chat_controller import ChatController
from backend.controllers.analytics_controller import AnalyticsController
from backend.controllers.network_controller import NetworkController
from backend.controllers.dashboard_controller import DashboardController
from backend.controllers.report_controller import ReportController
from backend.controllers.map_controller import MapController
from backend.utilities.logger import SystemLogger


class APIGateway:
    """Catalyst API Gateway router for SurakshaAI."""

    def __init__(self):
        self._controllers = {
            "auth": AuthController(),
            "chat": ChatController(),
            "analytics": AnalyticsController(),
            "network": NetworkController(),
            "dashboard": DashboardController(),
            "report": ReportController(),
            "map": MapController(),
        }
        SystemLogger.info("APIGateway initialized with all controllers.")

    async def route(self, request: Request, call_next=None) -> Response:
        """
        Route request to the appropriate controller based on path.
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/handler (for chaining)
            
        Returns:
            JSONResponse with controller result
        """
        path = request.url.path
        method = request.method
        segments = path.strip("/").split("/")

        SystemLogger.info(f"[{method}] {path} - Routing request...")

        # Validate API path
        if len(segments) < 2 or segments[0] != "api":
            return JSONResponse(
                status_code=404,
                content={"status": "error", "detail": "Invalid API path. Expected /api/..."}
            )

        resource = segments[1]
        controller = self._controllers.get(resource)

        if not controller:
            self._available_routes = list(self._controllers.keys())
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "detail": f"Resource '{resource}' not found",
                    "available_routes": self._available_routes
                }
            )

        # Extract path parameters (after /api/{resource}/)
        path_params = segments[2:] if len(segments) > 2 else []

        try:
            # Route to controller based on HTTP method
            if method == "GET":
                response_data = await controller.get(request, path_params)
            elif method == "POST":
                body = await request.json() if await request.body() else {}
                response_data = await controller.post(request, path_params, body)
            elif method == "PUT":
                body = await request.json() if await request.body() else {}
                response_data = await controller.put(request, path_params, body)
            elif method == "DELETE":
                response_data = await controller.delete(request, path_params)
            elif method == "PATCH":
                body = await request.json() if await request.body() else {}
                response_data = await controller.patch(request, path_params, body)
            else:
                return JSONResponse(
                    status_code=405,
                    content={"status": "error", "detail": f"Method {method} not allowed for /api/{resource}"}
                )

            SystemLogger.info(f"[{method}] {path} - Successfully routed to {resource} controller.")
            return JSONResponse(status_code=200, content=response_data)

        except HTTPException as he:
            SystemLogger.error(f"[{method}] {path} - HTTPException: {he.detail}")
            return JSONResponse(status_code=he.status_code, content={"status": "error", "detail": he.detail})
        except Exception as e:
            SystemLogger.error(f"[{method}] {path} - Unexpected error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "detail": str(e), "note": "Check server logs for trace."}
            )

    @property
    def available_routes(self) -> list:
        return list(self._controllers.keys())


# Singleton instance
api_gateway = APIGateway()
