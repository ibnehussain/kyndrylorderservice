"""Health check endpoints"""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])

settings = get_settings()


@router.get(
    "/",
    summary="Basic health check",
    description="Returns the health status of the service",
)
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get(
    "/ready",
    summary="Readiness check",
    description="Returns readiness status including database connectivity",
)
async def readiness_check():
    """Readiness check with database connectivity"""
    try:
        # In a real application, you would test database connectivity here
        # For now, we'll just return ready status
        return {
            "status": "ready",
            "service": settings.app_name,
            "version": settings.app_version,
            "database": "connected",
            "timestamp": "2026-01-21T10:00:00Z",
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "service": settings.app_name,
            "version": settings.app_version,
            "database": "disconnected",
            "error": str(e),
        }


@router.get(
    "/live",
    summary="Liveness check",
    description="Returns liveness status of the service",
)
async def liveness_check():
    """Liveness check endpoint"""
    return {
        "status": "alive",
        "service": settings.app_name,
        "version": settings.app_version,
    }
