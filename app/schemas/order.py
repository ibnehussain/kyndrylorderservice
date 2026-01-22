"""Request and response schemas for orders API"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.core.validators import DecimalValidator, InputSanitizer
from app.models.base import OrderStatus, PaymentMethod, PaymentStatus


class AddressSchema(BaseModel):
    """Address schema for API requests/responses"""

    street: str = Field(..., min_length=1, max_length=255, example="123 Main St")
    city: str = Field(..., min_length=1, max_length=100, example="Seattle")
    state: str = Field(..., min_length=2, max_length=50, example="WA")
    postal_code: str = Field(..., min_length=5, max_length=20, example="98101")
    country: str = Field(default="US", min_length=2, max_length=2, example="US")

    @validator("street", "city", "state")
    def sanitize_text_fields(cls, v):
        """Sanitize text fields to prevent XSS attacks"""
        return InputSanitizer.sanitize_text(v)

    @validator("postal_code", "country")
    def sanitize_code_fields(cls, v):
        """Sanitize code fields"""
        return InputSanitizer.sanitize_text(v)


class OrderItemCreate(BaseModel):
    """Schema for creating order items"""

    product_id: str = Field(..., min_length=1, example="prod_123")
    product_name: str = Field(
        ..., min_length=1, max_length=255, example="Premium Widget"
    )
    quantity: int = Field(..., ge=1, le=1000, example=2)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2, example=29.99)

    @validator("product_id", "product_name")
    def sanitize_text_fields(cls, v):
        """Sanitize text fields to prevent XSS attacks"""
        return InputSanitizer.sanitize_text(v)

    @validator("quantity")
    def validate_quantity(cls, v):
        """Validate quantity"""
        return DecimalValidator.validate_quantity(v)

    @validator("unit_price")
    def validate_unit_price(cls, v):
        """Validate unit price with decimal precision"""
        return DecimalValidator.validate_unit_price(v)


class OrderItemResponse(OrderItemCreate):
    """Schema for order item responses"""

    total_price: Decimal = Field(..., ge=0, decimal_places=2, example=59.98)

    @validator("total_price")
    def validate_total_price(cls, v):
        """Validate total price with decimal precision"""
        return DecimalValidator.validate_total_amount(v)


class PaymentInfoCreate(BaseModel):
    """Schema for payment information in requests"""

    method: PaymentMethod = Field(..., example=PaymentMethod.CREDIT_CARD)
    last_four_digits: Optional[str] = Field(
        None, min_length=4, max_length=4, example="1234"
    )

    @validator("last_four_digits")
    def sanitize_last_four_digits(cls, v):
        """Sanitize last four digits field"""
        if v is not None:
            return InputSanitizer.sanitize_text(v, max_length=4)
        return v


class PaymentInfoResponse(PaymentInfoCreate):
    """Schema for payment information in responses"""

    status: PaymentStatus = Field(..., example=PaymentStatus.PENDING)
    transaction_id: Optional[str] = Field(None, example="txn_abc123")
    processor: Optional[str] = Field(None, example="stripe")

    @validator("transaction_id", "processor")
    def sanitize_text_fields(cls, v):
        """Sanitize text fields"""
        if v is not None:
            return InputSanitizer.sanitize_text(v)
        return v


class OrderCreate(BaseModel):
    """Schema for creating new orders"""

    customer_id: str = Field(..., min_length=1, example="cust_456")
    customer_email: str = Field(
        ..., pattern=r"^[^@]+@[^@]+\.[^@]+$", example="customer@example.com"
    )
    items: List[OrderItemCreate] = Field(..., min_items=1, max_items=100)

    billing_address: AddressSchema
    shipping_address: Optional[AddressSchema] = None

    payment_info: PaymentInfoCreate

    tax_amount: Decimal = Field(
        default=Decimal("0.00"), ge=0, decimal_places=2, example=5.99
    )
    shipping_amount: Decimal = Field(
        default=Decimal("0.00"), ge=0, decimal_places=2, example=9.99
    )
    discount_amount: Decimal = Field(
        default=Decimal("0.00"), ge=0, decimal_places=2, example=0.00
    )

    notes: Optional[str] = Field(
        None, max_length=1000, example="Please handle with care"
    )
    source: str = Field(default="api", example="web")

    @validator("customer_id", "source")
    def sanitize_id_fields(cls, v):
        """Sanitize ID and source fields"""
        return InputSanitizer.sanitize_text(v)

    @validator("notes")
    def sanitize_notes(cls, v):
        """Sanitize notes field to prevent XSS"""
        if v is not None:
            return InputSanitizer.sanitize_text(v, max_length=1000)
        return v

    @validator("tax_amount", "shipping_amount", "discount_amount")
    def validate_financial_amounts(cls, v, values, **kwargs):
        """Validate financial amounts with decimal precision"""
        field_name = kwargs.get('field', {}).name if 'field' in kwargs else 'amount'
        return DecimalValidator.validate_financial_amount(
            v, field_name=field_name, allow_zero=True
        )

    class Config:
        schema_extra = {
            "example": {
                "customer_id": "cust_456",
                "customer_email": "john.doe@example.com",
                "items": [
                    {
                        "product_id": "prod_123",
                        "product_name": "Premium Widget",
                        "quantity": 2,
                        "unit_price": 29.99,
                    }
                ],
                "billing_address": {
                    "street": "123 Main St",
                    "city": "Seattle",
                    "state": "WA",
                    "postal_code": "98101",
                    "country": "US",
                },
                "payment_info": {"method": "credit_card", "last_four_digits": "1234"},
                "tax_amount": 5.99,
                "shipping_amount": 9.99,
                "notes": "Express delivery requested",
            }
        }


class OrderUpdate(BaseModel):
    """Schema for updating existing orders"""

    status: Optional[OrderStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)

    # Allow updating shipping address
    shipping_address: Optional[AddressSchema] = None

    @validator("notes")
    def sanitize_notes(cls, v):
        """Sanitize notes field to prevent XSS"""
        if v is not None:
            return InputSanitizer.sanitize_text(v, max_length=1000)
        return v


class OrderResponse(BaseModel):
    """Schema for order responses"""

    id: str = Field(..., example="order_789")
    order_number: str = Field(..., example="ORD-2026-001")
    customer_id: str = Field(..., example="cust_456")
    customer_email: str = Field(..., example="john.doe@example.com")

    status: OrderStatus = Field(..., example=OrderStatus.PENDING)
    items: List[OrderItemResponse]

    subtotal: Decimal = Field(..., example=59.98)
    tax_amount: Decimal = Field(..., example=5.99)
    shipping_amount: Decimal = Field(..., example=9.99)
    discount_amount: Decimal = Field(..., example=0.00)
    total_amount: Decimal = Field(..., example=75.96)
    currency: str = Field(..., example="USD")

    billing_address: AddressSchema
    shipping_address: Optional[AddressSchema] = None

    payment_info: PaymentInfoResponse

    notes: Optional[str] = None
    source: str = Field(..., example="api")

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}


class OrderListResponse(BaseModel):
    """Schema for paginated order list responses"""

    orders: List[OrderResponse]
    total_count: int = Field(..., example=150)
    page: int = Field(..., example=1)
    page_size: int = Field(..., example=20)
    total_pages: int = Field(..., example=8)


class MessageResponse(BaseModel):
    """Schema for simple message responses"""

    message: str = Field(..., example="Order created successfully")
    order_id: Optional[str] = Field(None, example="order_789")
