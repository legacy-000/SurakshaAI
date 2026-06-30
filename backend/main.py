import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Import main routers
from backend.routes import api_router
from backend.utilities.logger import SystemLogger

# Initialize FastAPI App
app = FastAPI(
    title="SURAKSHA AI - Backend Core",
    description="Crime Intelligence Platform for Karnataka Police",
    version="0.1.0",
)

# CORS Policy configuration
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
origins = [origin.strip() for origin in allowed_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_router)

@app.get("/")
def health_check():
    """
    Core System Health Check.
    Returns:
        JSON structure validating application status.
    """
    SystemLogger.info("Root health check request received.")
    return {
        "service": "SURAKSHA AI Backend",
        "status": "Running"
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    
    SystemLogger.info(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
