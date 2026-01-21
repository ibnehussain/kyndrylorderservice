"""Analytics service - Business logic for order analytics and reporting"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from app.models.analytics import (
    CustomerMetrics,
    DailyOrderMetrics,
    OrderStatusMetrics,
    RevenueMetrics,
)
from app.repositories.order_repository import OrderRepository
from app.schemas.analytics import (
    AnalyticsDateRange,
    AnalyticsSummaryResponse,
    DailyAnalyticsResponse,
    OrderStatusAnalyticsResponse,
    TopCustomersResponse,
)


class AnalyticsService:
    """Service for generating order analytics and metrics"""

    def __init__(self):
        self.order_repository = OrderRepository()

    def _fill_missing_days(
        self, daily_metrics: List[DailyOrderMetrics], start_date: date, end_date: date
    ) -> List[DailyOrderMetrics]:
        """Fill in missing days with zero metrics"""
        # Create a map of existing metrics by date
        metrics_by_date = {metric.date: metric for metric in daily_metrics}

        # Generate complete date range
        complete_metrics = []
        current_date = start_date

        while current_date <= end_date:
            if current_date in metrics_by_date:
                complete_metrics.append(metrics_by_date[current_date])
            else:
                # Create zero metric for missing day
                zero_metric = DailyOrderMetrics(
                    date=current_date,
                    order_count=0,
                    total_revenue=Decimal("0.00"),
                    average_order_value=Decimal("0.00"),
                    currency="USD",
                )
                complete_metrics.append(zero_metric)

            current_date += timedelta(days=1)

        return complete_metrics

    async def get_daily_analytics(
        self, date_range: AnalyticsDateRange
    ) -> DailyAnalyticsResponse:
        """Get daily analytics for the specified date range"""
        try:
            # Get daily metrics from repository
            daily_metrics = await self.order_repository.get_daily_metrics(
                date_range.start_date, date_range.end_date
            )

            # Fill missing days with zero metrics
            complete_metrics = self._fill_missing_days(
                daily_metrics, date_range.start_date, date_range.end_date
            )

            # Calculate period summary
            total_revenue, total_orders, avg_order_value = (
                await self.order_repository.get_revenue_summary(
                    date_range.start_date, date_range.end_date
                )
            )

            period_summary = RevenueMetrics(
                period_start=date_range.start_date,
                period_end=date_range.end_date,
                total_revenue=total_revenue,
                total_orders=total_orders,
                average_order_value=avg_order_value,
                currency="USD",
            )

            # Calculate total days
            total_days = (date_range.end_date - date_range.start_date).days + 1

            return DailyAnalyticsResponse(
                metrics=complete_metrics,
                period_summary=period_summary,
                total_days=total_days,
            )

        except Exception as e:
            raise RuntimeError(f"Failed to get daily analytics: {str(e)}")

    async def get_order_status_analytics(
        self, date_range: AnalyticsDateRange
    ) -> OrderStatusAnalyticsResponse:
        """Get order analytics grouped by status"""
        try:
            # Get status metrics
            status_metrics = await self.order_repository.get_order_status_metrics(
                date_range.start_date, date_range.end_date
            )

            # Calculate totals
            total_orders = sum(metric.count for metric in status_metrics)
            total_revenue = sum(metric.total_value for metric in status_metrics)

            return OrderStatusAnalyticsResponse(
                status_metrics=status_metrics,
                period=date_range,
                total_orders=total_orders,
                total_revenue=total_revenue,
            )

        except Exception as e:
            raise RuntimeError(f"Failed to get order status analytics: {str(e)}")

    async def get_top_customers(
        self, date_range: AnalyticsDateRange, limit: int = 10
    ) -> TopCustomersResponse:
        """Get top customers by total spending"""
        try:
            customer_metrics = await self.order_repository.get_customer_metrics(
                date_range.start_date, date_range.end_date, limit
            )

            return TopCustomersResponse(
                customers=customer_metrics, period=date_range, limit=limit
            )

        except Exception as e:
            raise RuntimeError(f"Failed to get top customers: {str(e)}")

    async def get_analytics_summary(
        self, date_range: AnalyticsDateRange
    ) -> AnalyticsSummaryResponse:
        """Get comprehensive analytics summary"""
        try:
            # Get all analytics components
            daily_analytics = await self.get_daily_analytics(date_range)
            status_analytics = await self.get_order_status_analytics(date_range)
            top_customers = await self.get_top_customers(date_range, limit=5)

            # Get additional insights
            busiest_day_result = await self.order_repository.get_busiest_day(
                date_range.start_date, date_range.end_date
            )

            highest_revenue_day_result = (
                await self.order_repository.get_highest_revenue_day(
                    date_range.start_date, date_range.end_date
                )
            )

            # Calculate growth rate (compare to previous period)
            growth_rate = await self._calculate_growth_rate(date_range)

            return AnalyticsSummaryResponse(
                period=date_range,
                revenue_metrics=daily_analytics.period_summary,
                status_breakdown=status_analytics.status_metrics,
                daily_trend=daily_analytics.metrics,
                top_customers=top_customers.customers,
                growth_rate=growth_rate,
                busiest_day=busiest_day_result[0] if busiest_day_result else None,
                highest_revenue_day=(
                    highest_revenue_day_result[0]
                    if highest_revenue_day_result
                    else None
                ),
            )

        except Exception as e:
            raise RuntimeError(f"Failed to get analytics summary: {str(e)}")

    async def _calculate_growth_rate(
        self, current_period: AnalyticsDateRange
    ) -> Optional[float]:
        """Calculate revenue growth rate compared to previous period"""
        try:
            # Calculate previous period (same length as current period)
            period_length = (
                current_period.end_date - current_period.start_date
            ).days + 1
            previous_end = current_period.start_date - timedelta(days=1)
            previous_start = previous_end - timedelta(days=period_length - 1)

            # Get revenue for both periods
            current_revenue, _, _ = await self.order_repository.get_revenue_summary(
                current_period.start_date, current_period.end_date
            )

            previous_revenue, _, _ = await self.order_repository.get_revenue_summary(
                previous_start, previous_end
            )

            # Calculate growth rate
            if previous_revenue > 0:
                growth_rate = (
                    (current_revenue - previous_revenue) / previous_revenue
                ) * 100
                return round(float(growth_rate), 2)

            return None

        except Exception:
            # Return None if we can't calculate growth rate
            return None

    async def get_revenue_trends(self, days: int = 30) -> DailyAnalyticsResponse:
        """Get revenue trends for the last N days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        date_range = AnalyticsDateRange(start_date=start_date, end_date=end_date)
        return await self.get_daily_analytics(date_range)

    async def get_customer_analytics(
        self, customer_id: str, date_range: Optional[AnalyticsDateRange] = None
    ) -> CustomerMetrics:
        """Get analytics for a specific customer"""
        if not date_range:
            # Default to last 12 months
            end_date = date.today()
            start_date = end_date.replace(year=end_date.year - 1)
            date_range = AnalyticsDateRange(start_date=start_date, end_date=end_date)

        try:
            customer_metrics = await self.order_repository.get_customer_metrics(
                date_range.start_date,
                date_range.end_date,
                limit=1000,  # Large limit to get all orders
            )

            # Find the specific customer
            for metric in customer_metrics:
                if metric.customer_id == customer_id:
                    return metric

            # If customer not found, return empty metrics
            return CustomerMetrics(
                customer_id=customer_id,
                customer_email="",
                total_orders=0,
                total_spent=Decimal("0.00"),
                average_order_value=Decimal("0.00"),
                first_order_date=None,
                last_order_date=None,
            )

        except Exception as e:
            raise RuntimeError(
                f"Failed to get customer analytics for {customer_id}: {str(e)}"
            )


# Dependency for FastAPI
def get_analytics_service() -> AnalyticsService:
    """FastAPI dependency to get analytics service instance"""
    return AnalyticsService()
