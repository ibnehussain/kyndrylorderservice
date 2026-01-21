"""Order-related data models"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from app.models.base import (
    OrderStatus, PaymentStatus, PaymentMethod, 
    TimestampMixin, generate_uuid
)


class Address(BaseModel):
    """Address model"""
    street: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    postal_code: str = Field(..., min_length=5, max_length=20)
    country: str = Field(default="US", min_length=2, max_length=2)


class OrderItem(BaseModel):
    """Individual order item"""
    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., ge=1, le=1000)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)
    total_price: Decimal = Field(..., ge=0, decimal_places=2)
    
    @validator('total_price')
    def validate_total_price(cls, v, values):
        """Validate that total_price equals quantity * unit_price"""
        if 'quantity' in values and 'unit_price' in values:
            expected_total = values['quantity'] * values['unit_price']
            if v != expected_total:
                raise ValueError(f"Total price {v} must equal quantity {values['quantity']} * unit_price {values['unit_price']}")
        return v


class PaymentInfo(BaseModel):
    """Payment information"""
    method: PaymentMethod
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    transaction_id: Optional[str] = None
    last_four_digits: Optional[str] = Field(None, min_length=4, max_length=4)
    processor: Optional[str] = None  # e.g., "stripe", "paypal"


class Order(TimestampMixin):
    """Complete order model for database storage"""
    
    # Cosmos DB specific fields
    id: str = Field(default_factory=generate_uuid, alias="_id")
    partition_key: str = Field(..., alias="partitionKey")  # customer_id for partitioning
    document_type: str = Field(default="order", alias="type")
    
    # Business fields
    order_number: str = Field(..., min_length=1, max_length=50)
    customer_id: str = Field(..., min_length=1)
    customer_email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    
    # Order details
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    items: List[OrderItem] = Field(..., min_items=1, max_items=100)
    
    # Pricing
    subtotal: Decimal = Field(..., ge=0, decimal_places=2)
    tax_amount: Decimal = Field(default=Decimal('0.00'), ge=0, decimal_places=2)
    shipping_amount: Decimal = Field(default=Decimal('0.00'), ge=0, decimal_places=2)
    discount_amount: Decimal = Field(default=Decimal('0.00'), ge=0, decimal_places=2)
    total_amount: Decimal = Field(..., ge=0, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    
    # Addresses
    billing_address: Address
    shipping_address: Optional[Address] = None
    
    # Payment
    payment_info: PaymentInfo
    
    # Metadata
    notes: Optional[str] = Field(None, max_length=1000)
    source: str = Field(default="api")  # web, mobile, api, etc.
    
    class Config:
        allow_population_by_field_name = True
        validate_assignment = True
        use_enum_values = True
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }
    
    @validator('partition_key')
    def set_partition_key(cls, v, values):
        """Set partition key to customer_id for optimal partitioning"""
        if 'customer_id' in values:
            return values['customer_id']
        return v
    
    @validator('total_amount')
    def validate_total_amount(cls, v, values):
        """Validate total amount calculation"""
        if all(field in values for field in ['subtotal', 'tax_amount', 'shipping_amount', 'discount_amount']):
            expected_total = (
                values['subtotal'] + 
                values['tax_amount'] + 
                values['shipping_amount'] - 
                values['discount_amount']
            )
            if abs(v - expected_total) > Decimal('0.01'):  # Allow for rounding differences
                raise ValueError(f"Total amount {v} does not match calculated total {expected_total}")
        return v
    
    @validator('subtotal')
    def validate_subtotal(cls, v, values):
        """Validate subtotal matches sum of item totals"""
        if 'items' in values:
            calculated_subtotal = sum(item.total_price for item in values['items'])
            if abs(v - calculated_subtotal) > Decimal('0.01'):
                raise ValueError(f"Subtotal {v} does not match sum of items {calculated_subtotal}")
        return v