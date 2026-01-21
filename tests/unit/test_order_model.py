"""Unit tests for Order model"""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.base import OrderStatus, PaymentMethod, PaymentStatus
from app.models.order import Address, Order, OrderItem, PaymentInfo


class TestOrderModel:
    """Test cases for Order model"""

    def test_order_creation_success(
        self, sample_address, sample_order_items, sample_payment_info
    ):
        """Test successful order creation with valid data"""
        # Act
        order = Order(
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
            billing_address=sample_address,
            shipping_address=sample_address,
            payment_info=sample_payment_info,
            created_at=datetime.utcnow(),
        )

        # Assert
        assert order.id == "order_123"
        assert order.customer_id == "cust_456"
        assert order.status == OrderStatus.PENDING
        assert len(order.items) == 2
        assert order.total_amount == Decimal("96.36")

    def test_order_validation_invalid_email(
        self, sample_address, sample_order_items, sample_payment_info
    ):
        """Test order validation with invalid email"""
        # Act & Assert
        with pytest.raises(ValidationError, match="regex"):
            Order(
                order_number="ORD-20260121-ABC123",
                customer_id="cust_456",
                customer_email="invalid-email",  # Invalid email format
                partition_key="cust_456",
                status=OrderStatus.PENDING,
                items=sample_order_items,
                subtotal=Decimal("79.97"),
                total_amount=Decimal("96.36"),
                billing_address=sample_address,
                payment_info=sample_payment_info,
            )

    def test_order_validation_empty_items(self, sample_address, sample_payment_info):
        """Test order validation with empty items list"""
        # Act & Assert
        with pytest.raises(ValidationError, match="min_items"):
            Order(
                order_number="ORD-20260121-ABC123",
                customer_id="cust_456",
                customer_email="test@example.com",
                partition_key="cust_456",
                status=OrderStatus.PENDING,
                items=[],  # Empty items list
                subtotal=Decimal("0.00"),
                total_amount=Decimal("0.00"),
                billing_address=sample_address,
                payment_info=sample_payment_info,
            )

    def test_order_total_amount_validation(
        self, sample_address, sample_order_items, sample_payment_info
    ):
        """Test order total amount validation"""
        # Act & Assert
        with pytest.raises(ValidationError, match="Total amount"):
            Order(
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
                total_amount=Decimal("50.00"),  # Incorrect total
                billing_address=sample_address,
                payment_info=sample_payment_info,
            )

    def test_order_subtotal_validation(self, sample_address, sample_payment_info):
        """Test order subtotal validation against item totals"""
        # Arrange
        items = [
            OrderItem(
                product_id="prod_1",
                product_name="Test Product",
                quantity=2,
                unit_price=Decimal("25.00"),
                total_price=Decimal("50.00"),
            )
        ]

        # Act & Assert
        with pytest.raises(ValidationError, match="Subtotal"):
            Order(
                order_number="ORD-20260121-ABC123",
                customer_id="cust_456",
                customer_email="test@example.com",
                partition_key="cust_456",
                status=OrderStatus.PENDING,
                items=items,
                subtotal=Decimal("100.00"),  # Incorrect subtotal
                total_amount=Decimal("100.00"),
                billing_address=sample_address,
                payment_info=sample_payment_info,
            )

    def test_order_partition_key_auto_set(
        self, sample_address, sample_order_items, sample_payment_info
    ):
        """Test that partition key is automatically set from customer_id"""
        # Act
        order = Order(
            order_number="ORD-20260121-ABC123",
            customer_id="cust_456",
            customer_email="test@example.com",
            # partition_key not provided - should be auto-set
            status=OrderStatus.PENDING,
            items=sample_order_items,
            subtotal=Decimal("79.97"),
            total_amount=Decimal("79.97"),
            billing_address=sample_address,
            payment_info=sample_payment_info,
        )

        # Assert
        assert order.partition_key == "cust_456"


class TestOrderItem:
    """Test cases for OrderItem model"""

    def test_order_item_creation_success(self):
        """Test successful order item creation"""
        # Act
        item = OrderItem(
            product_id="prod_123",
            product_name="Test Product",
            quantity=3,
            unit_price=Decimal("15.99"),
            total_price=Decimal("47.97"),
        )

        # Assert
        assert item.product_id == "prod_123"
        assert item.quantity == 3
        assert item.total_price == Decimal("47.97")

    def test_order_item_total_price_validation(self):
        """Test order item total price validation"""
        # Act & Assert
        with pytest.raises(ValidationError, match="Total price"):
            OrderItem(
                product_id="prod_123",
                product_name="Test Product",
                quantity=2,
                unit_price=Decimal("10.00"),
                total_price=Decimal("25.00"),  # Should be 20.00
            )

    def test_order_item_invalid_quantity(self):
        """Test order item with invalid quantity"""
        # Act & Assert
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            OrderItem(
                product_id="prod_123",
                product_name="Test Product",
                quantity=0,  # Invalid quantity
                unit_price=Decimal("10.00"),
                total_price=Decimal("0.00"),
            )


class TestAddress:
    """Test cases for Address model"""

    def test_address_creation_success(self):
        """Test successful address creation"""
        # Act
        address = Address(
            street="123 Main St",
            city="Seattle",
            state="WA",
            postal_code="98101",
            country="US",
        )

        # Assert
        assert address.street == "123 Main St"
        assert address.city == "Seattle"
        assert address.country == "US"

    def test_address_default_country(self):
        """Test address creation with default country"""
        # Act
        address = Address(
            street="123 Main St",
            city="Seattle",
            state="WA",
            postal_code="98101",
            # country not provided - should default to "US"
        )

        # Assert
        assert address.country == "US"

    def test_address_validation_empty_street(self):
        """Test address validation with empty street"""
        # Act & Assert
        with pytest.raises(ValidationError, match="min_length"):
            Address(
                street="",  # Empty street
                city="Seattle",
                state="WA",
                postal_code="98101",
            )


class TestPaymentInfo:
    """Test cases for PaymentInfo model"""

    def test_payment_info_creation_success(self):
        """Test successful payment info creation"""
        # Act
        payment = PaymentInfo(
            method=PaymentMethod.CREDIT_CARD,
            status=PaymentStatus.AUTHORIZED,
            transaction_id="txn_123",
            last_four_digits="1234",
        )

        # Assert
        assert payment.method == PaymentMethod.CREDIT_CARD
        assert payment.status == PaymentStatus.AUTHORIZED
        assert payment.last_four_digits == "1234"

    def test_payment_info_default_status(self):
        """Test payment info creation with default status"""
        # Act
        payment = PaymentInfo(
            method=PaymentMethod.PAYPAL
            # status not provided - should default to PENDING
        )

        # Assert
        assert payment.status == PaymentStatus.PENDING

    def test_payment_info_invalid_last_four_digits(self):
        """Test payment info with invalid last four digits"""
        # Act & Assert
        with pytest.raises(ValidationError, match="min_length"):
            PaymentInfo(
                method=PaymentMethod.CREDIT_CARD, last_four_digits="123"  # Too short
            )
