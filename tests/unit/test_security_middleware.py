"""Tests for security middleware"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.security import (
    RequestValidationMiddleware,
    SecurityHeadersMiddleware,
)


@pytest.fixture
def app_with_security_headers():
    """Create a test app with security headers middleware."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    return app


@pytest.fixture
def app_with_request_validation():
    """Create a test app with request validation middleware."""
    app = FastAPI()
    app.add_middleware(RequestValidationMiddleware, max_request_size=1000)

    @app.get("/test")
    async def test_get():
        return {"message": "test"}

    @app.post("/test")
    async def test_post(request: Request):
        return {"message": "test"}

    return app


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware."""

    def test_security_headers_present(self, app_with_security_headers):
        """Test that all security headers are present in response."""
        client = TestClient(app_with_security_headers)
        response = client.get("/test")

        assert response.status_code == 200
        
        # Check all security headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in response.headers["Strict-Transport-Security"]
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "geolocation=()" in response.headers["Permissions-Policy"]

    def test_security_headers_on_error_response(self, app_with_security_headers):
        """Test that security headers are present even on error responses."""
        client = TestClient(app_with_security_headers)
        response = client.get("/nonexistent")

        # Even on 404, security headers should be present
        assert response.status_code == 404
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers


class TestRequestValidationMiddleware:
    """Tests for RequestValidationMiddleware."""

    def test_request_too_large(self, app_with_request_validation):
        """Test that requests exceeding max size are rejected."""
        client = TestClient(app_with_request_validation)
        
        # Send a request with content-length exceeding limit
        response = client.post(
            "/test",
            json={"data": "test"},
            headers={"Content-Length": "2000"}
        )

        assert response.status_code == 413
        assert "Request too large" in response.json()["detail"]

    def test_request_within_size_limit(self, app_with_request_validation):
        """Test that requests within size limit are accepted."""
        client = TestClient(app_with_request_validation)
        
        response = client.post(
            "/test",
            json={"data": "test"},
            headers={"Content-Length": "100"}
        )

        assert response.status_code == 200

    def test_invalid_content_length_header(self, app_with_request_validation):
        """Test that invalid content-length header is rejected."""
        client = TestClient(app_with_request_validation)
        
        response = client.post(
            "/test",
            json={"data": "test"},
            headers={"Content-Length": "invalid"}
        )

        assert response.status_code == 400
        assert "Invalid Content-Length" in response.json()["detail"]

    def test_unsupported_content_type(self, app_with_request_validation):
        """Test that unsupported content types are rejected."""
        client = TestClient(app_with_request_validation)
        
        response = client.post(
            "/test",
            data="plain text data",
            headers={
                "Content-Type": "text/plain",
                "Content-Length": "15"
            }
        )

        assert response.status_code == 415
        assert "Unsupported Content-Type" in response.json()["detail"]

    def test_supported_content_type_json(self, app_with_request_validation):
        """Test that application/json content type is accepted."""
        client = TestClient(app_with_request_validation)
        
        response = client.post(
            "/test",
            json={"data": "test"}
        )

        assert response.status_code == 200

    def test_get_request_no_validation(self, app_with_request_validation):
        """Test that GET requests bypass content-type validation."""
        client = TestClient(app_with_request_validation)
        
        response = client.get("/test")

        assert response.status_code == 200

    def test_post_without_body(self, app_with_request_validation):
        """Test that POST without body is allowed."""
        client = TestClient(app_with_request_validation)
        
        # POST without content-length should pass
        response = client.post(
            "/test",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
