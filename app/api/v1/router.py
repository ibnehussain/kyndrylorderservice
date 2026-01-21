"""API v1 router configuration"""

from fastapi import APIRouter
from app.api.v1.endpoints import orders, health, analytics

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(orders.router)
api_router.include_router(health.router)
api_router.include_router(analytics.router)