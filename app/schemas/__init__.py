"""Schemas package initialization"""

from .analytics import (
    AnalyticsDateRange,
    AnalyticsQueryParams,
    AnalyticsSummaryResponse,
    DailyAnalyticsResponse,
    OrderStatusAnalyticsResponse,
    TopCustomersResponse,
)
from .order import (
    AddressSchema,
    MessageResponse,
    OrderCreate,
    OrderItemCreate,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
    OrderUpdate,
    PaymentInfoCreate,
    PaymentInfoResponse,
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
    "AnalyticsQueryParams",
]
