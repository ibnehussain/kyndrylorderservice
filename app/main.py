"""Main FastAPI application entry point"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.middleware.security import (
    RequestValidationMiddleware,
    SecurityHeadersMiddleware,
)

settings = get_settings()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A production-ready order management service",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add rate limiter state and error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security headers middleware (first to ensure all responses have security headers)
if settings.enable_security_headers:
    app.add_middleware(SecurityHeadersMiddleware)

# Add request validation middleware
app.add_middleware(RequestValidationMiddleware, max_request_size=settings.max_request_size)

# Add CORS middleware with enhanced production settings
# Note: For production, update allowed_hosts in config to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
@limiter.limit(settings.rate_limit_default)
async def root(request: Request):
    """Root endpoint with service information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "healthy",
        "docs_url": "/docs",
    }


@app.get("/health")
@limiter.limit(settings.rate_limit_default)
async def health_check(request: Request):
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
