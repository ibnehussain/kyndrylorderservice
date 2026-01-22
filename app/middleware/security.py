"""Security middleware for FastAPI application"""

from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Enforce HTTPS in production
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Prevent referrer leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Feature policy / Permissions policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate incoming requests."""

    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):
        """
        Initialize the middleware.
        
        Args:
            app: The FastAPI application
            max_request_size: Maximum allowed request size in bytes (default: 10MB)
        """
        super().__init__(app)
        self.max_request_size = max_request_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate incoming request."""
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                content_length_int = int(content_length)
                if content_length_int > self.max_request_size:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "detail": f"Request too large. Maximum size is {self.max_request_size} bytes"
                        },
                    )
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid Content-Length header"},
                )

        # Validate Content-Type for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "").lower()
            # Allow common content types
            allowed_content_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data",
            ]
            
            # Check if any allowed content type is present
            is_valid_content_type = any(
                allowed_type in content_type for allowed_type in allowed_content_types
            )
            
            # Only validate if there's a body (content-length > 0)
            if content_length and int(content_length) > 0 and not is_valid_content_type:
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={
                        "detail": "Unsupported Content-Type. Use application/json, "
                        "application/x-www-form-urlencoded, or multipart/form-data"
                    },
                )

        response = await call_next(request)
        return response
