"""Unit tests for AnalyticsService"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.services.analytics_service import AnalyticsService
from app.models.analytics import DailyOrderMetrics, OrderStatusMetrics, CustomerMetrics, RevenueMetrics
from app.schemas.analytics import AnalyticsDateRange
from app.repositories.order_repository import OrderRepository


class TestAnalyticsService:
    """Test cases for AnalyticsService"""

    @pytest.fixture
    def analytics_service_with_mock_repo(self, mock_order_repository):
        """Analytics service with mocked repository"""
        service = AnalyticsService()
        service.order_repository = mock_order_repository
        return service

    @pytest.fixture
    def sample_date_range(self):
        """Sample date range for testing"""
        return AnalyticsDateRange(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )

    @pytest.fixture
    def sample_daily_metrics(self):
        """Sample daily metrics data"""
        return [
            DailyOrderMetrics(
                date=date(2026, 1, 1),
                order_count=5,
                total_revenue=Decimal("250.00"),
                average_order_value=Decimal("50.00"),
                currency="USD"
            ),
            DailyOrderMetrics(
                date=date(2026, 1, 2),
                order_count=3,
                total_revenue=Decimal("150.00"),
                average_order_value=Decimal("50.00"),
                currency="USD"
            )
        ]

    @pytest.fixture
    def sample_status_metrics(self):
        """Sample status metrics data"""
        return [
            OrderStatusMetrics(
                status="pending",
                count=15,
                total_value=Decimal("750.00"),
                percentage=60.0
            ),
            OrderStatusMetrics(
                status="confirmed",
                count=8,
                total_value=Decimal("400.00"),
                percentage=32.0
            ),
            OrderStatusMetrics(
                status="cancelled",
                count=2,
                total_value=Decimal("100.00"),
                percentage=8.0
            )
        ]

    @pytest.fixture
    def sample_customer_metrics(self):
        """Sample customer metrics data"""
        return [
            CustomerMetrics(
                customer_id="cust_1",
                customer_email="customer1@example.com",
                total_orders=5,
                total_spent=Decimal("500.00"),
                average_order_value=Decimal("100.00"),
                first_order_date=datetime(2026, 1, 1),
                last_order_date=datetime(2026, 1, 15)
            ),
            CustomerMetrics(
                customer_id="cust_2",
                customer_email="customer2@example.com",
                total_orders=3,
                total_spent=Decimal("300.00"),
                average_order_value=Decimal("100.00"),
                first_order_date=datetime(2026, 1, 5),
                last_order_date=datetime(2026, 1, 20)
            )
        ]

    @pytest.mark.asyncio
    async def test_get_daily_analytics_success(self, analytics_service_with_mock_repo, 
                                              mock_order_repository, sample_date_range, 
                                              sample_daily_metrics):
        """Test successful daily analytics retrieval"""
        # Arrange
        mock_order_repository.get_daily_metrics.return_value = sample_daily_metrics
        mock_order_repository.get_revenue_summary.return_value = (
            Decimal("400.00"), 8, Decimal("50.00")
        )
        
        # Act
        result = await analytics_service_with_mock_repo.get_daily_analytics(sample_date_range)
        
        # Assert
        assert result is not None
        assert len(result.metrics) == 31  # Full month with filled missing days
        assert result.period_summary.total_revenue == Decimal("400.00")
        assert result.period_summary.total_orders == 8
        assert result.total_days == 31
        
        # Check that missing days are filled with zero metrics
        zero_day_found = any(metric.order_count == 0 for metric in result.metrics)
        assert zero_day_found
        
        mock_order_repository.get_daily_metrics.assert_called_once_with(
            sample_date_range.start_date, sample_date_range.end_date
        )

    @pytest.mark.asyncio
    async def test_get_order_status_analytics_success(self, analytics_service_with_mock_repo,
                                                     mock_order_repository, sample_date_range,
                                                     sample_status_metrics):
        """Test successful order status analytics retrieval"""
        # Arrange
        mock_order_repository.get_order_status_metrics.return_value = sample_status_metrics
        
        # Act
        result = await analytics_service_with_mock_repo.get_order_status_analytics(sample_date_range)
        
        # Assert
        assert result is not None
        assert len(result.status_metrics) == 3
        assert result.total_orders == 25  # 15 + 8 + 2
        assert result.total_revenue == Decimal("1250.00")  # 750 + 400 + 100
        assert result.period == sample_date_range
        
        mock_order_repository.get_order_status_metrics.assert_called_once_with(
            sample_date_range.start_date, sample_date_range.end_date
        )

    @pytest.mark.asyncio
    async def test_get_top_customers_success(self, analytics_service_with_mock_repo,
                                           mock_order_repository, sample_date_range,
                                           sample_customer_metrics):
        """Test successful top customers analytics retrieval"""
        # Arrange
        limit = 10
        mock_order_repository.get_customer_metrics.return_value = sample_customer_metrics
        
        # Act
        result = await analytics_service_with_mock_repo.get_top_customers(sample_date_range, limit)
        
        # Assert
        assert result is not None
        assert len(result.customers) == 2
        assert result.customers[0].customer_id == "cust_1"
        assert result.customers[0].total_spent == Decimal("500.00")
        assert result.limit == limit
        assert result.period == sample_date_range
        
        mock_order_repository.get_customer_metrics.assert_called_once_with(
            sample_date_range.start_date, sample_date_range.end_date, limit
        )

    @pytest.mark.asyncio
    async def test_get_analytics_summary_success(self, analytics_service_with_mock_repo,
                                               mock_order_repository, sample_date_range,
                                               sample_daily_metrics, sample_status_metrics,
                                               sample_customer_metrics):
        """Test successful analytics summary retrieval"""
        # Arrange
        mock_order_repository.get_daily_metrics.return_value = sample_daily_metrics
        mock_order_repository.get_revenue_summary.return_value = (
            Decimal("400.00"), 8, Decimal("50.00")
        )
        mock_order_repository.get_order_status_metrics.return_value = sample_status_metrics
        mock_order_repository.get_customer_metrics.return_value = sample_customer_metrics
        mock_order_repository.get_busiest_day.return_value = (date(2026, 1, 1), 5)
        mock_order_repository.get_highest_revenue_day.return_value = (date(2026, 1, 1), Decimal("250.00"))
        
        # Act
        result = await analytics_service_with_mock_repo.get_analytics_summary(sample_date_range)
        
        # Assert
        assert result is not None
        assert result.period == sample_date_range
        assert result.revenue_metrics.total_revenue == Decimal("400.00")
        assert len(result.status_breakdown) == 3
        assert len(result.daily_trend) == 31  # Full month
        assert len(result.top_customers) == 2
        assert result.busiest_day == date(2026, 1, 1)
        assert result.highest_revenue_day == date(2026, 1, 1)

    @pytest.mark.asyncio
    async def test_get_revenue_trends_success(self, analytics_service_with_mock_repo,
                                            mock_order_repository):
        """Test successful revenue trends retrieval"""
        # Arrange
        days = 7
        mock_order_repository.get_daily_metrics.return_value = []
        mock_order_repository.get_revenue_summary.return_value = (
            Decimal("0.00"), 0, Decimal("0.00")
        )
        
        # Act
        result = await analytics_service_with_mock_repo.get_revenue_trends(days)
        
        # Assert
        assert result is not None
        assert result.total_days == days
        assert len(result.metrics) == days  # Should have metrics for all days (with zeros)
        
        # Verify the date range is correct (last 7 days)
        expected_end = date.today()
        expected_start = expected_end - timedelta(days=days - 1)
        
        mock_order_repository.get_daily_metrics.assert_called_once_with(
            expected_start, expected_end
        )

    @pytest.mark.asyncio
    async def test_get_customer_analytics_existing_customer(self, analytics_service_with_mock_repo,
                                                          mock_order_repository,
                                                          sample_customer_metrics):
        """Test getting analytics for an existing customer"""
        # Arrange
        customer_id = "cust_1"
        mock_order_repository.get_customer_metrics.return_value = sample_customer_metrics
        
        # Act
        result = await analytics_service_with_mock_repo.get_customer_analytics(customer_id)
        
        # Assert
        assert result is not None
        assert result.customer_id == customer_id
        assert result.customer_email == "customer1@example.com"
        assert result.total_orders == 5
        assert result.total_spent == Decimal("500.00")

    @pytest.mark.asyncio
    async def test_get_customer_analytics_nonexistent_customer(self, analytics_service_with_mock_repo,
                                                             mock_order_repository):
        """Test getting analytics for a non-existent customer"""
        # Arrange
        customer_id = "nonexistent_customer"
        mock_order_repository.get_customer_metrics.return_value = []
        
        # Act
        result = await analytics_service_with_mock_repo.get_customer_analytics(customer_id)
        
        # Assert
        assert result is not None
        assert result.customer_id == customer_id
        assert result.customer_email == ""
        assert result.total_orders == 0
        assert result.total_spent == Decimal("0.00")

    def test_fill_missing_days(self, analytics_service_with_mock_repo):
        """Test filling missing days with zero metrics"""
        # Arrange
        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 5)
        partial_metrics = [
            DailyOrderMetrics(
                date=date(2026, 1, 1),
                order_count=5,
                total_revenue=Decimal("100.00"),
                average_order_value=Decimal("20.00"),
                currency="USD"
            ),
            DailyOrderMetrics(
                date=date(2026, 1, 3),
                order_count=3,
                total_revenue=Decimal("60.00"),
                average_order_value=Decimal("20.00"),
                currency="USD"
            )
        ]
        
        # Act
        result = analytics_service_with_mock_repo._fill_missing_days(
            partial_metrics, start_date, end_date
        )
        
        # Assert
        assert len(result) == 5  # 5 days total
        assert result[0].date == date(2026, 1, 1)
        assert result[0].order_count == 5  # Original data
        assert result[1].date == date(2026, 1, 2)
        assert result[1].order_count == 0   # Filled zero
        assert result[2].date == date(2026, 1, 3)
        assert result[2].order_count == 3   # Original data
        assert result[3].date == date(2026, 1, 4)
        assert result[3].order_count == 0   # Filled zero
        assert result[4].date == date(2026, 1, 5)
        assert result[4].order_count == 0   # Filled zero

    @pytest.mark.asyncio
    async def test_calculate_growth_rate_with_previous_data(self, analytics_service_with_mock_repo,
                                                          mock_order_repository):
        """Test growth rate calculation with previous period data"""
        # Arrange
        current_period = AnalyticsDateRange(
            start_date=date(2026, 1, 15),
            end_date=date(2026, 1, 21)  # 7 days
        )
        
        # Mock current period revenue: $1000
        # Mock previous period revenue: $800
        # Expected growth rate: 25%
        mock_order_repository.get_revenue_summary.side_effect = [
            (Decimal("1000.00"), 10, Decimal("100.00")),  # Current period
            (Decimal("800.00"), 8, Decimal("100.00"))     # Previous period
        ]
        
        # Act
        result = await analytics_service_with_mock_repo._calculate_growth_rate(current_period)
        
        # Assert
        assert result == 25.0
        assert mock_order_repository.get_revenue_summary.call_count == 2

    @pytest.mark.asyncio
    async def test_calculate_growth_rate_with_zero_previous_revenue(self, analytics_service_with_mock_repo,
                                                                  mock_order_repository):
        """Test growth rate calculation when previous period has zero revenue"""
        # Arrange
        current_period = AnalyticsDateRange(
            start_date=date(2026, 1, 15),
            end_date=date(2026, 1, 21)
        )
        
        mock_order_repository.get_revenue_summary.side_effect = [
            (Decimal("1000.00"), 10, Decimal("100.00")),  # Current period
            (Decimal("0.00"), 0, Decimal("0.00"))         # Previous period (zero)
        ]
        
        # Act
        result = await analytics_service_with_mock_repo._calculate_growth_rate(current_period)
        
        # Assert
        assert result is None  # Should return None when previous revenue is zero

    @pytest.mark.asyncio
    async def test_analytics_service_error_handling(self, analytics_service_with_mock_repo,
                                                   mock_order_repository, sample_date_range):
        """Test error handling in analytics service"""
        # Arrange
        mock_order_repository.get_daily_metrics.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to get daily analytics"):
            await analytics_service_with_mock_repo.get_daily_analytics(sample_date_range)