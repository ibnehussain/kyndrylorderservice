"""Request and response schemas for orders API"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.base import OrderStatus, PaymentStatus, PaymentMethod


class AddressSchema(BaseModel):
    """Address schema for API requests/responses"""
    street: str = Field(..., min_length=1, max_length=255, example="123 Main St")
    city: str = Field(..., min_length=1, max_length=100, example="Seattle")
    state: str = Field(..., min_length=2, max_length=50, example="WA")
    postal_code: str = Field(..., min_length=5, max_length=20, example="98101")
    country: str = Field(default="US", min_length=2, max_length=2, example="US")


class OrderItemCreate(BaseModel):
    """Schema for creating order items"""
    product_id: str = Field(..., min_length=1, example="prod_123")
    product_name: str = Field(..., min_length=1, max_length=255, example="Premium Widget")
    quantity: int = Field(..., ge=1, le=1000, example=2)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2, example=29.99)


class OrderItemResponse(OrderItemCreate):
    """Schema for order item responses"""
    total_price: Decimal = Field(..., ge=0, decimal_places=2, example=59.98)


class PaymentInfoCreate(BaseModel):
    """Schema for payment information in requests"""
    method: PaymentMethod = Field(..., example=PaymentMethod.CREDIT_CARD)
    last_four_digits: Optional[str] = Field(None, min_length=4, max_length=4, example="1234")


class PaymentInfoResponse(PaymentInfoCreate):
    """Schema for payment information in responses"""
    status: PaymentStatus = Field(..., example=PaymentStatus.PENDING)
    transaction_id: Optional[str] = Field(None, example="txn_abc123")
    processor: Optional[str] = Field(None, example="stripe")


class OrderCreate(BaseModel):
    """Schema for creating new orders"""
    customer_id: str = Field(..., min_length=1, example="cust_456")
    customer_email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$', example="customer@example.com")
    items: List[OrderItemCreate] = Field(..., min_items=1, max_items=100)
    
    billing_address: AddressSchema
    shipping_address: Optional[AddressSchema] = None
    
    payment_info: PaymentInfoCreate
    
    tax_amount: Decimal = Field(default=Decimal('0.00'), ge=0, decimal_places=2, example=5.99)
    shipping_amount: Decimal = Field(default=Decimal('0.00'), ge=0, decimal_places=2, example=9.99)
    discount_amount: Decimal = Field(default=Decimal('0.00'), ge=0, decimal_places=2, example=0.00)
    
    notes: Optional[str] = Field(None, max_length=1000, example="Please handle with care")
    source: str = Field(default="api", example="web")

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
                        "unit_price": 29.99
                    }
                ],
                "billing_address": {
                    "street": "123 Main St",
                    "city": "Seattle",
                    "state": "WA",
                    "postal_code": "98101",
                    "country": "US"
                },
                "payment_info": {
                    "method": "credit_card",
                    "last_four_digits": "1234"
                },
                "tax_amount": 5.99,
                "shipping_amount": 9.99,
                "notes": "Express delivery requested"
            }
        }


class OrderUpdate(BaseModel):
    """Schema for updating existing orders"""
    status: Optional[OrderStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)
    
    # Allow updating shipping address
    shipping_address: Optional[AddressSchema] = None


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
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


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