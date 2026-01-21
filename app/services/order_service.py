"""Order service - Business logic layer for order management"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from app.models.order import Order, OrderItem, Address, PaymentInfo
from app.models.base import OrderStatus, PaymentStatus
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderCreate, OrderUpdate


class OrderService:
    """Business logic service for order operations"""
    
    def __init__(self):
        self.order_repository = OrderRepository()
    
    def _generate_order_number(self) -> str:
        """Generate a unique order number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"ORD-{timestamp}-{random_suffix}"
    
    def _calculate_order_totals(self, items: List[OrderItem], 
                               tax_amount: Decimal = Decimal('0.00'),
                               shipping_amount: Decimal = Decimal('0.00'),
                               discount_amount: Decimal = Decimal('0.00')) -> tuple[Decimal, Decimal]:
        """Calculate subtotal and total amount for an order"""
        subtotal = sum(item.total_price for item in items)
        total_amount = subtotal + tax_amount + shipping_amount - discount_amount
        return subtotal, total_amount
    
    def _create_order_items_from_schema(self, items_data: List[dict]) -> List[OrderItem]:
        """Convert order item schema data to OrderItem models"""
        order_items = []
        for item_data in items_data:
            total_price = item_data['quantity'] * item_data['unit_price']
            order_item = OrderItem(
                product_id=item_data['product_id'],
                product_name=item_data['product_name'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=total_price
            )
            order_items.append(order_item)
        return order_items
    
    async def create_order(self, order_data: OrderCreate) -> Order:
        """Create a new order"""
        try:
            # Convert items data to OrderItem models
            order_items = []
            for item_data in order_data.items:
                total_price = item_data.quantity * item_data.unit_price
                order_item = OrderItem(
                    product_id=item_data.product_id,
                    product_name=item_data.product_name,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    total_price=total_price
                )
                order_items.append(order_item)
            
            # Calculate totals
            subtotal, total_amount = self._calculate_order_totals(
                order_items,
                order_data.tax_amount,
                order_data.shipping_amount, 
                order_data.discount_amount
            )
            
            # Create addresses
            billing_address = Address(**order_data.billing_address.dict())
            shipping_address = None
            if order_data.shipping_address:
                shipping_address = Address(**order_data.shipping_address.dict())
            else:
                # Use billing address as shipping address if not provided
                shipping_address = billing_address
            
            # Create payment info
            payment_info = PaymentInfo(
                method=order_data.payment_info.method,
                status=PaymentStatus.PENDING,
                last_four_digits=order_data.payment_info.last_four_digits
            )
            
            # Create order
            order = Order(
                order_number=self._generate_order_number(),
                customer_id=order_data.customer_id,
                customer_email=order_data.customer_email,
                partition_key=order_data.customer_id,  # Use customer_id as partition key
                status=OrderStatus.PENDING,
                items=order_items,
                subtotal=subtotal,
                tax_amount=order_data.tax_amount,
                shipping_amount=order_data.shipping_amount,
                discount_amount=order_data.discount_amount,
                total_amount=total_amount,
                billing_address=billing_address,
                shipping_address=shipping_address,
                payment_info=payment_info,
                notes=order_data.notes,
                source=order_data.source,
                created_at=datetime.utcnow()
            )
            
            # Save to repository
            created_order = await self.order_repository.create(order)
            
            # In a real system, you would trigger payment processing,
            # inventory reservation, and send notifications here
            await self._process_order_async(created_order)
            
            return created_order
            
        except Exception as e:
            raise RuntimeError(f"Failed to create order: {str(e)}")
    
    async def get_order(self, order_id: str, customer_id: str) -> Optional[Order]:
        """Get an order by ID and customer ID"""
        return await self.order_repository.get_by_id(order_id, customer_id)
    
    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Get an order by order number"""
        return await self.order_repository.get_order_by_number(order_number)
    
    async def update_order(self, order_id: str, customer_id: str, 
                          update_data: OrderUpdate) -> Optional[Order]:
        """Update an existing order"""
        try:
            # Get existing order
            existing_order = await self.order_repository.get_by_id(order_id, customer_id)
            if not existing_order:
                return None
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            
            for field, value in update_dict.items():
                if field == "shipping_address" and value:
                    setattr(existing_order, field, Address(**value))
                else:
                    setattr(existing_order, field, value)
            
            existing_order.updated_at = datetime.utcnow()
            
            # Save changes
            updated_order = await self.order_repository.update(existing_order)
            
            # Trigger status change processing if needed
            if "status" in update_dict:
                await self._handle_status_change(updated_order, update_dict["status"])
            
            return updated_order
            
        except Exception as e:
            raise RuntimeError(f"Failed to update order {order_id}: {str(e)}")
    
    async def cancel_order(self, order_id: str, customer_id: str) -> Optional[Order]:
        """Cancel an order"""
        try:
            existing_order = await self.order_repository.get_by_id(order_id, customer_id)
            if not existing_order:
                return None
            
            # Check if order can be cancelled
            if existing_order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
                raise ValueError(f"Cannot cancel order in status: {existing_order.status}")
            
            existing_order.status = OrderStatus.CANCELLED
            existing_order.updated_at = datetime.utcnow()
            
            updated_order = await self.order_repository.update(existing_order)
            
            # In a real system, you would:
            # - Refund payment if captured
            # - Release inventory
            # - Send cancellation notification
            await self._handle_order_cancellation(updated_order)
            
            return updated_order
            
        except Exception as e:
            raise RuntimeError(f"Failed to cancel order {order_id}: {str(e)}")
    
    async def delete_order(self, order_id: str, customer_id: str) -> bool:
        """Delete an order (admin operation)"""
        return await self.order_repository.delete(order_id, customer_id)
    
    async def list_orders(self, customer_id: Optional[str] = None,
                         status: Optional[OrderStatus] = None,
                         page: int = 1,
                         page_size: int = 20) -> tuple[List[Order], int]:
        """List orders with pagination"""
        try:
            offset = (page - 1) * page_size
            
            if status:
                orders = await self.order_repository.get_orders_by_status(
                    status, customer_id, page_size
                )
            else:
                orders = await self.order_repository.list_items(
                    customer_id, page_size, offset
                )
            
            total_count = await self.order_repository.count_orders(customer_id)
            
            return orders, total_count
            
        except Exception as e:
            raise RuntimeError(f"Failed to list orders: {str(e)}")
    
    async def get_customer_orders(self, customer_id: str, 
                                 page: int = 1, 
                                 page_size: int = 20) -> tuple[List[Order], int]:
        """Get all orders for a specific customer"""
        return await self.list_orders(customer_id=customer_id, page=page, page_size=page_size)
    
    async def _process_order_async(self, order: Order) -> None:
        """Async order processing (placeholder for real implementations)"""
        # In a real system, this would:
        # 1. Validate inventory availability
        # 2. Reserve inventory
        # 3. Process payment authorization
        # 4. Send order confirmation email
        # 5. Update order status to CONFIRMED
        
        # For demo purposes, just log
        print(f"Processing order {order.order_number} for customer {order.customer_id}")
    
    async def _handle_status_change(self, order: Order, new_status: OrderStatus) -> None:
        """Handle order status changes"""
        # In a real system, different status changes would trigger different actions
        if new_status == OrderStatus.CONFIRMED:
            # Send confirmation email, update inventory
            print(f"Order {order.order_number} confirmed")
        elif new_status == OrderStatus.SHIPPED:
            # Send shipping notification, update tracking
            print(f"Order {order.order_number} shipped")
        elif new_status == OrderStatus.DELIVERED:
            # Send delivery confirmation
            print(f"Order {order.order_number} delivered")
    
    async def _handle_order_cancellation(self, order: Order) -> None:
        """Handle order cancellation processing"""
        # In a real system:
        # 1. Process refund if payment was captured
        # 2. Release reserved inventory
        # 3. Send cancellation email
        # 4. Update analytics
        
        print(f"Order {order.order_number} cancelled")


# Dependency for FastAPI
def get_order_service() -> OrderService:
    """FastAPI dependency to get order service instance"""
    return OrderService()