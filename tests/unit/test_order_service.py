"""Unit tests for OrderService"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.services.order_service import OrderService
from app.models.order import Order
from app.models.base import OrderStatus, PaymentStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderItemCreate, AddressSchema, PaymentInfoCreate


class TestOrderService:
    """Test cases for OrderService"""

    @pytest.mark.asyncio
    async def test_create_order_success(self, order_service_with_mock_repo, mock_order_repository):
        """Test successful order creation"""
        # Arrange
        order_data = OrderCreate(
            customer_id="cust_123",
            customer_email="test@example.com",
            items=[
                OrderItemCreate(
                    product_id="prod_1",
                    product_name="Test Product",
                    quantity=2,
                    unit_price=Decimal("25.00")
                )
            ],
            billing_address=AddressSchema(
                street="123 Test St",
                city="Test City",
                state="TS", 
                postal_code="12345"
            ),
            payment_info=PaymentInfoCreate(
                method="credit_card",
                last_four_digits="1234"
            ),
            tax_amount=Decimal("5.00"),
            shipping_amount=Decimal("10.00")
        )
        
        # Mock repository response
        created_order = Order(
            id="order_123",
            order_number="ORD-20260121-TEST",
            customer_id="cust_123", 
            customer_email="test@example.com",
            partition_key="cust_123",
            status=OrderStatus.PENDING,
            items=order_data.items,
            subtotal=Decimal("50.00"),
            tax_amount=Decimal("5.00"),
            shipping_amount=Decimal("10.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("65.00"),
            billing_address=order_data.billing_address,
            payment_info=order_data.payment_info,
            created_at=datetime.utcnow()
        )
        
        mock_order_repository.create.return_value = created_order
        
        # Act
        result = await order_service_with_mock_repo.create_order(order_data)
        
        # Assert
        assert result is not None
        assert result.customer_id == "cust_123"
        assert result.status == OrderStatus.PENDING
        assert len(result.items) == 1
        assert result.total_amount == Decimal("65.00")
        mock_order_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_order_success(self, order_service_with_mock_repo, mock_order_repository, sample_order):
        """Test successful order retrieval"""
        # Arrange
        mock_order_repository.get_by_id.return_value = sample_order
        
        # Act
        result = await order_service_with_mock_repo.get_order("order_123", "cust_456")
        
        # Assert
        assert result is not None
        assert result.id == "order_123"
        assert result.customer_id == "cust_456"
        mock_order_repository.get_by_id.assert_called_once_with("order_123", "cust_456")

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, order_service_with_mock_repo, mock_order_repository):
        """Test order retrieval when order doesn't exist"""
        # Arrange
        mock_order_repository.get_by_id.return_value = None
        
        # Act
        result = await order_service_with_mock_repo.get_order("nonexistent", "cust_456")
        
        # Assert
        assert result is None
        mock_order_repository.get_by_id.assert_called_once_with("nonexistent", "cust_456")

    @pytest.mark.asyncio
    async def test_update_order_status(self, order_service_with_mock_repo, mock_order_repository, sample_order):
        """Test updating order status"""
        # Arrange
        mock_order_repository.get_by_id.return_value = sample_order
        updated_order = sample_order.copy()
        updated_order.status = OrderStatus.CONFIRMED
        mock_order_repository.update.return_value = updated_order
        
        update_data = OrderUpdate(status=OrderStatus.CONFIRMED)
        
        # Act
        result = await order_service_with_mock_repo.update_order("order_123", "cust_456", update_data)
        
        # Assert
        assert result is not None
        assert result.status == OrderStatus.CONFIRMED
        mock_order_repository.get_by_id.assert_called_once()
        mock_order_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_order_success(self, order_service_with_mock_repo, mock_order_repository, sample_order):
        """Test successful order cancellation"""
        # Arrange
        mock_order_repository.get_by_id.return_value = sample_order
        cancelled_order = sample_order.copy()
        cancelled_order.status = OrderStatus.CANCELLED
        mock_order_repository.update.return_value = cancelled_order
        
        # Act
        result = await order_service_with_mock_repo.cancel_order("order_123", "cust_456")
        
        # Assert
        assert result is not None
        assert result.status == OrderStatus.CANCELLED
        mock_order_repository.get_by_id.assert_called_once()
        mock_order_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_shipped_order_fails(self, order_service_with_mock_repo, mock_order_repository, sample_order):
        """Test that shipped orders cannot be cancelled"""
        # Arrange
        sample_order.status = OrderStatus.SHIPPED
        mock_order_repository.get_by_id.return_value = sample_order
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Cannot cancel order in status"):
            await order_service_with_mock_repo.cancel_order("order_123", "cust_456")

    @pytest.mark.asyncio
    async def test_list_orders_with_pagination(self, order_service_with_mock_repo, mock_order_repository, sample_order):
        """Test listing orders with pagination"""
        # Arrange
        orders = [sample_order]
        mock_order_repository.list_items.return_value = orders
        mock_order_repository.count_orders.return_value = 1
        
        # Act
        result_orders, total_count = await order_service_with_mock_repo.list_orders(
            customer_id="cust_456", page=1, page_size=20
        )
        
        # Assert
        assert len(result_orders) == 1
        assert total_count == 1
        assert result_orders[0].id == "order_123"
        mock_order_repository.list_items.assert_called_once()
        mock_order_repository.count_orders.assert_called_once()

    @pytest.mark.asyncio 
    async def test_delete_order_success(self, order_service_with_mock_repo, mock_order_repository):
        """Test successful order deletion"""
        # Arrange
        mock_order_repository.delete.return_value = True
        
        # Act
        result = await order_service_with_mock_repo.delete_order("order_123", "cust_456")
        
        # Assert
        assert result is True
        mock_order_repository.delete.assert_called_once_with("order_123", "cust_456")

    @pytest.mark.asyncio
    async def test_get_order_by_number(self, order_service_with_mock_repo, mock_order_repository, sample_order):
        """Test getting order by order number"""
        # Arrange
        mock_order_repository.get_order_by_number.return_value = sample_order
        
        # Act
        result = await order_service_with_mock_repo.get_order_by_number("ORD-20260121-ABC123")
        
        # Assert
        assert result is not None
        assert result.order_number == "ORD-20260121-ABC123"
        mock_order_repository.get_order_by_number.assert_called_once_with("ORD-20260121-ABC123")

    def test_generate_order_number(self, order_service_with_mock_repo):
        """Test order number generation"""
        # Act
        order_number = order_service_with_mock_repo._generate_order_number()
        
        # Assert
        assert order_number.startswith("ORD-")
        assert len(order_number) == 21  # ORD- + YYYYMMDD + - + 8 chars

    def test_calculate_order_totals(self, order_service_with_mock_repo, sample_order_items):
        """Test order total calculations"""
        # Act
        subtotal, total = order_service_with_mock_repo._calculate_order_totals(
            sample_order_items,
            tax_amount=Decimal("6.40"),
            shipping_amount=Decimal("9.99"),
            discount_amount=Decimal("5.00")
        )
        
        # Assert
        assert subtotal == Decimal("79.97")  # 59.98 + 19.99
        assert total == Decimal("91.36")     # 79.97 + 6.40 + 9.99 - 5.00