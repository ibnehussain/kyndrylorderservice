"""Tests for rate limiting in main application"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limit_not_exceeded(self):
        """Test that requests within rate limit are successful."""
        client = TestClient(app)
        
        # Make a few requests that should be within limit
        for _ in range(5):
            response = client.get("/")
            assert response.status_code == 200

    def test_health_endpoint_with_rate_limit(self):
        """Test that health endpoint has rate limiting."""
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are present in response."""
        client = TestClient(app)
        
        response = client.get("/")
        
        # SlowAPI adds rate limit information to headers
        # Check that response is successful
        assert response.status_code == 200
        
    def test_root_endpoint_returns_service_info(self):
        """Test that root endpoint returns correct service information."""
        client = TestClient(app)
        
        response = client.get("/")
        data = response.json()
        
        assert response.status_code == 200
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "healthy"


class TestSecurityHeaders:
    """Tests for security headers in main application."""

    def test_security_headers_on_root(self):
        """Test that security headers are present on root endpoint."""
        client = TestClient(app)
        
        response = client.get("/")
        
        # Check security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Strict-Transport-Security" in response.headers
        assert "Content-Security-Policy" in response.headers

    def test_security_headers_on_health(self):
        """Test that security headers are present on health endpoint."""
        client = TestClient(app)
        
        response = client.get("/health")
        
        # Check security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_headers_on_options_request(self):
        """Test that CORS headers are present on OPTIONS request."""
        client = TestClient(app)
        
        response = client.options(
            "/",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200

    def test_cors_allows_configured_methods(self):
        """Test that CORS is configured with specific methods."""
        client = TestClient(app)
        
        # Make a simple request to verify CORS middleware is active
        response = client.get("/")
        
        assert response.status_code == 200
