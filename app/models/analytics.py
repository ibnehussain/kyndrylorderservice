"""Analytics data models for order metrics"""

from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.base import TimestampMixin


class DailyOrderMetrics(BaseModel):
    """Daily order analytics metrics"""

    date: date_type = Field(..., description="Date for the metrics")
    order_count: int = Field(
        ..., ge=0, description="Total number of orders for the day"
    )
    total_revenue: Decimal = Field(
        ..., ge=0, decimal_places=2, description="Total revenue for the day"
    )
    average_order_value: Decimal = Field(
        ..., ge=0, decimal_places=2, description="Average order value for the day"
    )
    currency: str = Field(
        default="USD", min_length=3, max_length=3, description="Currency code"
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v), date_type: lambda v: v.isoformat()}


class OrderStatusMetrics(BaseModel):
    """Order metrics grouped by status"""

    status: str = Field(..., description="Order status")
    count: int = Field(..., ge=0, description="Number of orders with this status")
    total_value: Decimal = Field(
        ...,
        ge=0,
        decimal_places=2,
        description="Total value of orders with this status",
    )
    percentage: float = Field(
        ..., ge=0, le=100, description="Percentage of total orders"
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class CustomerMetrics(BaseModel):
    """Customer-related analytics metrics"""

    customer_id: str = Field(..., description="Customer ID")
    customer_email: str = Field(..., description="Customer email")
    total_orders: int = Field(
        ..., ge=0, description="Total number of orders for this customer"
    )
    total_spent: Decimal = Field(
        ..., ge=0, decimal_places=2, description="Total amount spent by this customer"
    )
    average_order_value: Decimal = Field(
        ..., ge=0, decimal_places=2, description="Average order value for this customer"
    )
    first_order_date: Optional[datetime] = Field(
        None, description="Date of first order"
    )
    last_order_date: Optional[datetime] = Field(None, description="Date of last order")

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}


class RevenueMetrics(BaseModel):
    """Revenue analytics metrics"""

    period_start: date_type = Field(..., description="Start date of the period")
    period_end: date_type = Field(..., description="End date of the period")
    total_revenue: Decimal = Field(
        ..., ge=0, decimal_places=2, description="Total revenue for the period"
    )
    total_orders: int = Field(
        ..., ge=0, description="Total number of orders for the period"
    )
    average_order_value: Decimal = Field(
        ..., ge=0, decimal_places=2, description="Average order value for the period"
    )
    currency: str = Field(
        default="USD", min_length=3, max_length=3, description="Currency code"
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v), date_type: lambda v: v.isoformat()}
