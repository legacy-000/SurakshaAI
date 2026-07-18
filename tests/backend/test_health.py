import pytest

pytestmark = pytest.mark.skip(
    reason="Backend is a Zoho Catalyst serverless function, not FastAPI. "
           "No /backend/main.py module. Health check covered by common/health/."
)
