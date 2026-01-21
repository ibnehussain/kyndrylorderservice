"""Pytest configuration and fixtures"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime
from typing import Generator
from unittest.mock import AsyncMock, Mock

from app.models.order import Order, OrderItem, Address, PaymentInfo
from app.models.base import OrderStatus, PaymentStatus, PaymentMethod
from app.services.order_service import OrderService
from app.services.analytics_service import AnalyticsService
from app.repositories.order_repository import OrderRepository


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_address() -> Address:
    """Fixture for sample address data"""
    return Address(
        street="123 Main St",
        city="Seattle", 
        state="WA",
        postal_code="98101",
        country="US"
    )


@pytest.fixture
def sample_order_items() -> list[OrderItem]:
    """Fixture for sample order items"""
    return [
        OrderItem(
            product_id="prod_123",
            product_name="Premium Widget",
            quantity=2,
            unit_price=Decimal("29.99"),
            total_price=Decimal("59.98")
        ),
        OrderItem(
            product_id="prod_456", 
            product_name="Standard Widget",
            quantity=1,
            unit_price=Decimal("19.99"),
            total_price=Decimal("19.99")
        )
    ]


@pytest.fixture
def sample_payment_info() -> PaymentInfo:
    """Fixture for sample payment information"""
    return PaymentInfo(
        method=PaymentMethod.CREDIT_CARD,
        status=PaymentStatus.PENDING,
        last_four_digits="1234"
    )


@pytest.fixture
def sample_order(sample_address, sample_order_items, sample_payment_info) -> Order:
    """Fixture for sample order"""
    return Order(
        id="order_123",
        order_number="ORD-20260121-ABC123", 
        customer_id="cust_456",
        customer_email="test@example.com",
        partition_key="cust_456",
        status=OrderStatus.PENDING,
        items=sample_order_items,
        subtotal=Decimal("79.97"),
        tax_amount=Decimal("6.40"),
        shipping_amount=Decimal("9.99"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("96.36"),
        currency="USD",
        billing_address=sample_address,
        shipping_address=sample_address,
        payment_info=sample_payment_info,
        notes="Test order",
        source="test",
        created_at=datetime.utcnow()
    )


@pytest.fixture
def mock_order_repository() -> Mock:
    """Mock order repository for testing"""
    mock_repo = Mock(spec=OrderRepository)
    
    # Configure async methods as AsyncMock
    mock_repo.create = AsyncMock()
    mock_repo.get_by_id = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.delete = AsyncMock()
    mock_repo.list_items = AsyncMock()
    mock_repo.get_orders_by_status = AsyncMock()
    mock_repo.count_orders = AsyncMock()
    mock_repo.get_order_by_number = AsyncMock()
    
    # Analytics methods
    mock_repo.get_daily_metrics = AsyncMock()
    mock_repo.get_order_status_metrics = AsyncMock()
    mock_repo.get_customer_metrics = AsyncMock()
    mock_repo.get_revenue_summary = AsyncMock()
    mock_repo.get_busiest_day = AsyncMock()
    mock_repo.get_highest_revenue_day = AsyncMock()
    
    return mock_repo


@pytest.fixture
def order_service_with_mock_repo(mock_order_repository) -> OrderService:
    """Order service with mocked repository"""
    service = OrderService()
    service.order_repository = mock_order_repository
    return service


@pytest.fixture
def analytics_service_with_mock_repo(mock_order_repository) -> AnalyticsService:
    """Analytics service with mocked repository"""
    service = AnalyticsService()
    service.order_repository = mock_order_repository
    return service


class AsyncIterator:
    """Helper class for async iteration in tests"""
    def __init__(self, seq):
        self.iter = iter(seq)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration