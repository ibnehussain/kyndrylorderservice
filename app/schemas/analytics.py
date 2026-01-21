"""Request and response schemas for analytics API"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.models.analytics import (
    CustomerMetrics,
    DailyOrderMetrics,
    OrderStatusMetrics,
    RevenueMetrics,
)


class AnalyticsDateRange(BaseModel):
    """Date range for analytics queries"""

    start_date: date = Field(..., description="Start date for analytics (inclusive)")
    end_date: date = Field(..., description="End date for analytics (inclusive)")

    @validator("end_date")
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date"""
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("end_date must be after or equal to start_date")
        return v

    @validator("start_date", "end_date")
    def validate_not_future(cls, v):
        """Validate that dates are not in the future"""
        if v > date.today():
            raise ValueError("Date cannot be in the future")
        return v


class DailyAnalyticsResponse(BaseModel):
    """Response schema for daily analytics"""

    metrics: List[DailyOrderMetrics] = Field(
        ..., description="Daily metrics for the requested period"
    )
    period_summary: RevenueMetrics = Field(
        ..., description="Summary metrics for the entire period"
    )
    total_days: int = Field(..., ge=0, description="Total number of days in the period")


class OrderStatusAnalyticsResponse(BaseModel):
    """Response schema for order status analytics"""

    status_metrics: List[OrderStatusMetrics] = Field(
        ..., description="Metrics grouped by order status"
    )
    period: AnalyticsDateRange = Field(..., description="Date range for the analytics")
    total_orders: int = Field(
        ..., ge=0, description="Total number of orders in the period"
    )
    total_revenue: Decimal = Field(
        ..., ge=0, decimal_places=2, description="Total revenue in the period"
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class TopCustomersResponse(BaseModel):
    """Response schema for top customers analytics"""

    customers: List[CustomerMetrics] = Field(
        ..., description="Top customers by total spent"
    )
    period: AnalyticsDateRange = Field(..., description="Date range for the analytics")
    limit: int = Field(..., ge=1, description="Maximum number of customers returned")


class AnalyticsSummaryResponse(BaseModel):
    """Response schema for overall analytics summary"""

    period: AnalyticsDateRange = Field(..., description="Date range for the analytics")
    revenue_metrics: RevenueMetrics = Field(..., description="Revenue summary")
    status_breakdown: List[OrderStatusMetrics] = Field(
        ..., description="Orders by status"
    )
    daily_trend: List[DailyOrderMetrics] = Field(..., description="Daily metrics trend")
    top_customers: List[CustomerMetrics] = Field(
        ..., description="Top 5 customers by spending"
    )

    # Additional summary fields
    growth_rate: Optional[float] = Field(
        None, description="Revenue growth rate compared to previous period"
    )
    busiest_day: Optional[date] = Field(
        None, description="Day with highest order count"
    )
    highest_revenue_day: Optional[date] = Field(
        None, description="Day with highest revenue"
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v), date: lambda v: v.isoformat()}


class AnalyticsQueryParams(BaseModel):
    """Query parameters for analytics endpoints"""

    start_date: Optional[date] = Field(
        None, description="Start date (defaults to 30 days ago)"
    )
    end_date: Optional[date] = Field(None, description="End date (defaults to today)")
    customer_id: Optional[str] = Field(None, description="Filter by specific customer")
    limit: int = Field(default=10, ge=1, le=100, description="Limit for result sets")

    @validator("start_date", "end_date", pre=True)
    def parse_dates(cls, v):
        """Parse date strings to date objects"""
        if isinstance(v, str):
            return datetime.fromisoformat(v).date()
        return v

    def get_date_range(self) -> AnalyticsDateRange:
        """Get validated date range with defaults"""
        end_date = self.end_date or date.today()
        start_date = self.start_date or date.today().replace(
            day=1
        )  # First day of current month

        return AnalyticsDateRange(start_date=start_date, end_date=end_date)
