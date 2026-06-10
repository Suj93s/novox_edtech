from fastapi import APIRouter
from models.domain import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint to ensure the service is running."""
    return HealthResponse(status="ok")
