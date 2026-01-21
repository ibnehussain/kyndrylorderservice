"""Unit tests for Analytics API endpoints"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.analytics import DailyOrderMetrics, RevenueMetrics


class TestAnalyticsAPI:
    """Test cases for Analytics API endpoints"""

    @pytest.fixture
    def client(self):
        """Test client for the FastAPI application"""
        return TestClient(app)

    @pytest.fixture
    def mock_analytics_service(self):
        """Mock analytics service"""
        with patch("app.api.v1.endpoints.analytics.get_analytics_service") as mock:
            service_mock = AsyncMock()
            mock.return_value = service_mock
            yield service_mock

    def test_get_daily_analytics_success(self, client, mock_analytics_service):
        """Test successful daily analytics endpoint"""
        # Arrange
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        mock_response = {
            "metrics": [
                {
                    "date": start_date.isoformat(),
                    "order_count": 5,
                    "total_revenue": 250.00,
                    "average_order_value": 50.00,
                    "currency": "USD",
                }
            ],
            "period_summary": {
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_revenue": 250.00,
                "total_orders": 5,
                "average_order_value": 50.00,
                "currency": "USD",
            },
            "total_days": 8,
        }

        mock_analytics_service.get_daily_analytics.return_value = type(
            "MockResponse", (), mock_response
        )()

        # Act
        response = client.get(
            "/api/v1/analytics/daily",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "period_summary" in data
        assert data["total_days"] == 8

    def test_get_daily_analytics_default_dates(self, client, mock_analytics_service):
        """Test daily analytics with default date range"""
        # Arrange
        mock_response = {
            "metrics": [],
            "period_summary": {
                "period_start": "2026-01-01",
                "period_end": "2026-01-21",
                "total_revenue": 0.00,
                "total_orders": 0,
                "average_order_value": 0.00,
                "currency": "USD",
            },
            "total_days": 21,
        }

        mock_analytics_service.get_daily_analytics.return_value = type(
            "MockResponse", (), mock_response
        )()

        # Act
        response = client.get("/api/v1/analytics/daily")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "period_summary" in data

    def test_get_daily_analytics_invalid_date_range(
        self, client, mock_analytics_service
    ):
        """Test daily analytics with invalid date range"""
        # Arrange
        start_date = date.today()
        end_date = date.today() - timedelta(days=1)  # End before start

        # Act
        response = client.get(
            "/api/v1/analytics/daily",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        # Assert
        assert response.status_code == 400
        assert (
            "Start date must be before or equal to end date"
            in response.json()["detail"]
        )

    def test_get_daily_analytics_future_date(self, client, mock_analytics_service):
        """Test daily analytics with future end date"""
        # Arrange
        future_date = date.today() + timedelta(days=1)

        # Act
        response = client.get(
            "/api/v1/analytics/daily", params={"end_date": future_date.isoformat()}
        )

        # Assert
        assert response.status_code == 400
        assert "End date cannot be in the future" in response.json()["detail"]

    def test_get_order_status_analytics_success(self, client, mock_analytics_service):
        """Test successful order status analytics endpoint"""
        # Arrange
        mock_response = {
            "status_metrics": [
                {
                    "status": "pending",
                    "count": 15,
                    "total_value": 750.00,
                    "percentage": 60.0,
                },
                {
                    "status": "confirmed",
                    "count": 10,
                    "total_value": 500.00,
                    "percentage": 40.0,
                },
            ],
            "period": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
            "total_orders": 25,
            "total_revenue": 1250.00,
        }

        mock_analytics_service.get_order_status_analytics.return_value = type(
            "MockResponse", (), mock_response
        )()

        # Act
        response = client.get("/api/v1/analytics/orders/status")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status_metrics" in data
        assert "total_orders" in data
        assert data["total_orders"] == 25
        assert data["total_revenue"] == 1250.00

    def test_get_top_customers_analytics_success(self, client, mock_analytics_service):
        """Test successful top customers analytics endpoint"""
        # Arrange
        mock_response = {
            "customers": [
                {
                    "customer_id": "cust_1",
                    "customer_email": "customer1@example.com",
                    "total_orders": 5,
                    "total_spent": 500.00,
                    "average_order_value": 100.00,
                    "first_order_date": "2026-01-01T10:00:00Z",
                    "last_order_date": "2026-01-15T10:00:00Z",
                }
            ],
            "period": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
            "limit": 10,
        }

        mock_analytics_service.get_top_customers.return_value = type(
            "MockResponse", (), mock_response
        )()

        # Act
        response = client.get("/api/v1/analytics/customers/top", params={"limit": 10})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "customers" in data
        assert len(data["customers"]) == 1
        assert data["limit"] == 10

    def test_get_analytics_summary_success(self, client, mock_analytics_service):
        """Test successful analytics summary endpoint"""
        # Arrange
        mock_response = {
            "period": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
            "revenue_metrics": {
                "period_start": "2026-01-01",
                "period_end": "2026-01-31",
                "total_revenue": 1000.00,
                "total_orders": 20,
                "average_order_value": 50.00,
                "currency": "USD",
            },
            "status_breakdown": [],
            "daily_trend": [],
            "top_customers": [],
            "growth_rate": 15.5,
            "busiest_day": "2026-01-15",
            "highest_revenue_day": "2026-01-15",
        }

        mock_analytics_service.get_analytics_summary.return_value = type(
            "MockResponse", (), mock_response
        )()

        # Act
        response = client.get("/api/v1/analytics/summary")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "revenue_metrics" in data
        assert data["growth_rate"] == 15.5
        assert data["busiest_day"] == "2026-01-15"

    def test_get_revenue_trends_success(self, client, mock_analytics_service):
        """Test successful revenue trends endpoint"""
        # Arrange
        mock_response = {
            "metrics": [
                {
                    "date": "2026-01-21",
                    "order_count": 3,
                    "total_revenue": 150.00,
                    "average_order_value": 50.00,
                    "currency": "USD",
                }
            ],
            "period_summary": {
                "period_start": "2026-01-14",
                "period_end": "2026-01-21",
                "total_revenue": 150.00,
                "total_orders": 3,
                "average_order_value": 50.00,
                "currency": "USD",
            },
            "total_days": 7,
        }

        mock_analytics_service.get_revenue_trends.return_value = type(
            "MockResponse", (), mock_response
        )()

        # Act
        response = client.get("/api/v1/analytics/revenue/trends", params={"days": 7})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert data["total_days"] == 7

    def test_get_customer_analytics_success(self, client, mock_analytics_service):
        """Test successful customer analytics endpoint"""
        # Arrange
        customer_id = "cust_123"
        mock_response = {
            "customer_id": customer_id,
            "customer_email": "customer@example.com",
            "total_orders": 10,
            "total_spent": 1000.00,
            "average_order_value": 100.00,
            "first_order_date": "2025-01-01T10:00:00Z",
            "last_order_date": "2026-01-15T10:00:00Z",
        }

        mock_analytics_service.get_customer_analytics.return_value = type(
            "MockResponse", (), mock_response
        )()

        # Act
        response = client.get(f"/api/v1/analytics/customers/{customer_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["customer_id"] == customer_id
        assert data["total_orders"] == 10
        assert data["total_spent"] == 1000.00

    def test_get_today_analytics_success(self, client, mock_analytics_service):
        """Test successful today's analytics endpoint"""
        # Arrange
        today = date.today()
        mock_response = {
            "metrics": [
                {
                    "date": today.isoformat(),
                    "order_count": 2,
                    "total_revenue": 100.00,
                    "average_order_value": 50.00,
                    "currency": "USD",
                }
            ],
            "period_summary": {
                "period_start": today.isoformat(),
                "period_end": today.isoformat(),
                "total_revenue": 100.00,
                "total_orders": 2,
                "average_order_value": 50.00,
                "currency": "USD",
            },
            "total_days": 1,
        }

        mock_analytics_service.get_daily_analytics.return_value = type(
            "MockResponse", (), mock_response
        )()

        # Act
        response = client.get("/api/v1/analytics/quick/today")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_days"] == 1
        assert len(data["metrics"]) == 1

    def test_get_week_analytics_success(self, client, mock_analytics_service):
        """Test successful week analytics endpoint"""
        # Arrange
        mock_response = {
            "metrics": [],
            "period_summary": {
                "period_start": "2026-01-15",
                "period_end": "2026-01-21",
                "total_revenue": 0.00,
                "total_orders": 0,
                "average_order_value": 0.00,
                "currency": "USD",
            },
            "total_days": 7,
        }

        mock_analytics_service.get_revenue_trends.return_value = type(
            "MockResponse", (), mock_response
        )()

        # Act
        response = client.get("/api/v1/analytics/quick/week")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_days"] == 7

    def test_get_month_analytics_summary_success(self, client, mock_analytics_service):
        """Test successful month analytics summary endpoint"""
        # Arrange
        mock_response = {
            "period": {"start_date": "2026-01-01", "end_date": "2026-01-21"},
            "revenue_metrics": {
                "period_start": "2026-01-01",
                "period_end": "2026-01-21",
                "total_revenue": 1500.00,
                "total_orders": 30,
                "average_order_value": 50.00,
                "currency": "USD",
            },
            "status_breakdown": [],
            "daily_trend": [],
            "top_customers": [],
            "growth_rate": None,
            "busiest_day": None,
            "highest_revenue_day": None,
        }

        mock_analytics_service.get_analytics_summary.return_value = type(
            "MockResponse", (), mock_response
        )()

        # Act
        response = client.get("/api/v1/analytics/quick/month")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "revenue_metrics" in data
        assert data["revenue_metrics"]["total_orders"] == 30

    def test_analytics_service_error_handling(self, client, mock_analytics_service):
        """Test error handling in analytics endpoints"""
        # Arrange
        mock_analytics_service.get_daily_analytics.side_effect = Exception(
            "Service error"
        )

        # Act
        response = client.get("/api/v1/analytics/daily")

        # Assert
        assert response.status_code == 500
        assert "Failed to get daily analytics" in response.json()["detail"]

    def test_analytics_endpoint_parameter_validation(
        self, client, mock_analytics_service
    ):
        """Test parameter validation in analytics endpoints"""
        # Test invalid limit parameter
        response = client.get("/api/v1/analytics/customers/top", params={"limit": 0})
        assert response.status_code == 422  # Validation error

        # Test invalid days parameter
        response = client.get("/api/v1/analytics/revenue/trends", params={"days": 0})
        assert response.status_code == 422  # Validation error

        # Test limit too high
        response = client.get("/api/v1/analytics/customers/top", params={"limit": 200})
        assert response.status_code == 422  # Validation error
