import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.routes import api_router
from backend.utilities.logger import SystemLogger

app = FastAPI(
    title="SURAKSHA AI - Backend Core",
    description="Crime Intelligence Platform for Karnataka Police",
    version="0.1.0",
)

allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
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

# Mangum adapter for Catalyst Serverless Functions (ASGI -> WSGI bridge)
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    handler = None

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    SystemLogger.info(f"Starting server on {host}:{port}")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
