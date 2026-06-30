from fastapi import APIRouter
from .auth import router as auth_router
from .chat import router as chat_router
from .network import router as network_router
from .analytics import router as analytics_router
from .map import router as map_router
from .report import router as report_router
from .dashboard import router as dashboard_router

# Core system router
api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(network_router)
api_router.include_router(analytics_router)
api_router.include_router(map_router)
api_router.include_router(report_router)
api_router.include_router(dashboard_router)
