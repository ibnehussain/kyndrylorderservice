"""Schemas package initialization"""

from .order import (
    OrderCreate,
    OrderUpdate, 
    OrderResponse,
    OrderListResponse,
    MessageResponse,
    AddressSchema,
    OrderItemCreate,
    OrderItemResponse,
    PaymentInfoCreate,
    PaymentInfoResponse
)
from .analytics import (
    AnalyticsDateRange,
    DailyAnalyticsResponse,
    OrderStatusAnalyticsResponse,
    TopCustomersResponse,
    AnalyticsSummaryResponse,
    AnalyticsQueryParams
)

__all__ = [
    "OrderCreate",
    "OrderUpdate",
    "OrderResponse", 
    "OrderListResponse",
    "MessageResponse",
    "AddressSchema",
    "OrderItemCreate",
    "OrderItemResponse",
    "PaymentInfoCreate",
    "PaymentInfoResponse",
    "AnalyticsDateRange",
    "DailyAnalyticsResponse",
    "OrderStatusAnalyticsResponse",
    "TopCustomersResponse",
    "AnalyticsSummaryResponse",
    "AnalyticsQueryParams"
]