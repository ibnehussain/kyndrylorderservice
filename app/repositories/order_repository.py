"""Order repository implementation for Azure Cosmos DB"""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.models.analytics import CustomerMetrics, DailyOrderMetrics, OrderStatusMetrics
from app.models.base import OrderStatus
from app.models.order import Order
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """Repository for order operations with Azure Cosmos DB"""

    def _order_from_dict(self, data: Dict[str, Any]) -> Order:
        """Convert Cosmos DB document to Order model"""
        # Handle Decimal conversion
        for field in [
            "subtotal",
            "tax_amount",
            "shipping_amount",
            "discount_amount",
            "total_amount",
        ]:
            if field in data:
                data[field] = Decimal(str(data[field]))

        # Handle nested item total_price conversion
        if "items" in data:
            for item in data["items"]:
                if "total_price" in item:
                    item["total_price"] = Decimal(str(item["total_price"]))
                if "unit_price" in item:
                    item["unit_price"] = Decimal(str(item["unit_price"]))

        # Convert datetime strings back to datetime objects if needed
        for field in ["created_at", "updated_at"]:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(
                        data[field].replace("Z", "+00:00")
                    )
                except:
                    pass

        return Order(**data)

    def _order_to_dict(self, order: Order) -> Dict[str, Any]:
        """Convert Order model to Cosmos DB document format"""
        data = order.dict(by_alias=True)

        # Convert Decimal to float for Cosmos DB storage
        for field in [
            "subtotal",
            "tax_amount",
            "shipping_amount",
            "discount_amount",
            "total_amount",
        ]:
            if field in data and isinstance(data[field], Decimal):
                data[field] = float(data[field])

        # Handle nested items
        if "items" in data:
            for item in data["items"]:
                if "total_price" in item and isinstance(item["total_price"], Decimal):
                    item["total_price"] = float(item["total_price"])
                if "unit_price" in item and isinstance(item["unit_price"], Decimal):
                    item["unit_price"] = float(item["unit_price"])

        # Ensure datetime objects are ISO formatted
        for field in ["created_at", "updated_at"]:
            if field in data and isinstance(data[field], datetime):
                data[field] = data[field].isoformat()

        return data

    async def create(self, order: Order) -> Order:
        """Create a new order"""
        try:
            # Ensure database and container exist
            await self.create_database_if_not_exists()
            await self.create_container_if_not_exists()

            order_dict = self._order_to_dict(order)
            created_item = self.container.create_item(order_dict)
            return self._order_from_dict(created_item)
        except Exception as e:
            raise RuntimeError(f"Failed to create order: {str(e)}")

    async def get_by_id(self, order_id: str, customer_id: str) -> Optional[Order]:
        """Get order by ID and customer ID (partition key)"""
        try:
            item = self.container.read_item(item=order_id, partition_key=customer_id)
            return self._order_from_dict(item)
        except CosmosResourceNotFoundError:
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to get order {order_id}: {str(e)}")

    async def update(self, order: Order) -> Order:
        """Update an existing order"""
        try:
            order.updated_at = datetime.utcnow()
            order_dict = self._order_to_dict(order)

            updated_item = self.container.replace_item(item=order.id, body=order_dict)
            return self._order_from_dict(updated_item)
        except CosmosResourceNotFoundError:
            raise ValueError(f"Order {order.id} not found")
        except Exception as e:
            raise RuntimeError(f"Failed to update order {order.id}: {str(e)}")

    async def delete(self, order_id: str, customer_id: str) -> bool:
        """Delete an order"""
        try:
            self.container.delete_item(item=order_id, partition_key=customer_id)
            return True
        except CosmosResourceNotFoundError:
            return False
        except Exception as e:
            raise RuntimeError(f"Failed to delete order {order_id}: {str(e)}")

    async def list_items(
        self, customer_id: Optional[str] = None, max_items: int = 100, offset: int = 0
    ) -> List[Order]:
        """List orders with optional customer filter and pagination"""
        try:
            if customer_id:
                # Query orders for specific customer
                query = f"""
                    SELECT * FROM c 
                    WHERE c.type = 'order' 
                    AND c.partitionKey = '{customer_id}'
                    ORDER BY c.created_at DESC
                    OFFSET {offset} LIMIT {max_items}
                """
            else:
                # Query all orders (cross-partition)
                query = f"""
                    SELECT * FROM c 
                    WHERE c.type = 'order'
                    ORDER BY c.created_at DESC
                    OFFSET {offset} LIMIT {max_items}
                """

            items = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )

            return [self._order_from_dict(item) for item in items]
        except Exception as e:
            raise RuntimeError(f"Failed to list orders: {str(e)}")

    async def get_orders_by_status(
        self,
        status: OrderStatus,
        customer_id: Optional[str] = None,
        max_items: int = 100,
    ) -> List[Order]:
        """Get orders by status"""
        try:
            if customer_id:
                query = f"""
                    SELECT * FROM c 
                    WHERE c.type = 'order' 
                    AND c.partitionKey = '{customer_id}'
                    AND c.status = '{status.value}'
                    ORDER BY c.created_at DESC
                """
            else:
                query = f"""
                    SELECT * FROM c 
                    WHERE c.type = 'order'
                    AND c.status = '{status.value}'
                    ORDER BY c.created_at DESC
                """

            items = list(
                self.container.query_items(
                    query=query,
                    enable_cross_partition_query=True,
                    max_item_count=max_items,
                )
            )

            return [self._order_from_dict(item) for item in items]
        except Exception as e:
            raise RuntimeError(f"Failed to get orders by status {status}: {str(e)}")

    async def count_orders(self, customer_id: Optional[str] = None) -> int:
        """Count total orders"""
        try:
            if customer_id:
                query = f"""
                    SELECT VALUE COUNT(1) FROM c 
                    WHERE c.type = 'order' 
                    AND c.partitionKey = '{customer_id}'
                """
            else:
                query = """
                    SELECT VALUE COUNT(1) FROM c 
                    WHERE c.type = 'order'
                """

            result = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )

            return result[0] if result else 0
        except Exception as e:
            raise RuntimeError(f"Failed to count orders: {str(e)}")

    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number (cross-partition query)"""
        try:
            query = f"""
                SELECT * FROM c 
                WHERE c.type = 'order' 
                AND c.order_number = '{order_number}'
            """

            items = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True, max_item_count=1
                )
            )

            if items:
                return self._order_from_dict(items[0])
            return None
        except Exception as e:
            raise RuntimeError(
                f"Failed to get order by number {order_number}: {str(e)}"
            )

    # Analytics Methods

    async def get_daily_metrics(
        self, start_date: date, end_date: date
    ) -> List[DailyOrderMetrics]:
        """Get daily order metrics for a date range"""
        try:
            query = f"""
                SELECT 
                    SUBSTRING(c.created_at, 0, 10) as date,
                    COUNT(1) as order_count,
                    SUM(c.total_amount) as total_revenue,
                    AVG(c.total_amount) as average_order_value,
                    c.currency
                FROM c 
                WHERE c.type = 'order'
                AND c.created_at >= '{start_date}T00:00:00Z'
                AND c.created_at < '{end_date}T23:59:59Z'
                GROUP BY SUBSTRING(c.created_at, 0, 10), c.currency
                ORDER BY SUBSTRING(c.created_at, 0, 10)
            """

            items = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )

            daily_metrics = []
            for item in items:
                daily_metrics.append(
                    DailyOrderMetrics(
                        date=datetime.fromisoformat(item["date"]).date(),
                        order_count=item["order_count"],
                        total_revenue=Decimal(str(item["total_revenue"])),
                        average_order_value=Decimal(str(item["average_order_value"])),
                        currency=item["currency"],
                    )
                )

            return daily_metrics

        except Exception as e:
            raise RuntimeError(f"Failed to get daily metrics: {str(e)}")

    async def get_order_status_metrics(
        self, start_date: date, end_date: date
    ) -> List[OrderStatusMetrics]:
        """Get order metrics grouped by status"""
        try:
            # First get total count for percentage calculation
            total_query = f"""
                SELECT COUNT(1) as total_count, SUM(c.total_amount) as total_value
                FROM c 
                WHERE c.type = 'order'
                AND c.created_at >= '{start_date}T00:00:00Z'
                AND c.created_at < '{end_date}T23:59:59Z'
            """

            total_result = list(
                self.container.query_items(
                    query=total_query, enable_cross_partition_query=True
                )
            )

            total_orders = total_result[0]["total_count"] if total_result else 0

            # Get metrics by status
            query = f"""
                SELECT 
                    c.status,
                    COUNT(1) as count,
                    SUM(c.total_amount) as total_value
                FROM c 
                WHERE c.type = 'order'
                AND c.created_at >= '{start_date}T00:00:00Z'
                AND c.created_at < '{end_date}T23:59:59Z'
                GROUP BY c.status
                ORDER BY COUNT(1) DESC
            """

            items = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )

            status_metrics = []
            for item in items:
                percentage = (
                    (item["count"] / total_orders * 100) if total_orders > 0 else 0
                )
                status_metrics.append(
                    OrderStatusMetrics(
                        status=item["status"],
                        count=item["count"],
                        total_value=Decimal(str(item["total_value"])),
                        percentage=round(percentage, 2),
                    )
                )

            return status_metrics

        except Exception as e:
            raise RuntimeError(f"Failed to get order status metrics: {str(e)}")

    async def get_customer_metrics(
        self, start_date: date, end_date: date, limit: int = 10
    ) -> List[CustomerMetrics]:
        """Get top customer metrics by total spending"""
        try:
            query = f"""
                SELECT 
                    c.customer_id,
                    c.customer_email,
                    COUNT(1) as total_orders,
                    SUM(c.total_amount) as total_spent,
                    AVG(c.total_amount) as average_order_value,
                    MIN(c.created_at) as first_order_date,
                    MAX(c.created_at) as last_order_date
                FROM c 
                WHERE c.type = 'order'
                AND c.created_at >= '{start_date}T00:00:00Z'
                AND c.created_at < '{end_date}T23:59:59Z'
                GROUP BY c.customer_id, c.customer_email
                ORDER BY SUM(c.total_amount) DESC
                OFFSET 0 LIMIT {limit}
            """

            items = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )

            customer_metrics = []
            for item in items:
                first_order_date = None
                last_order_date = None

                if item.get("first_order_date"):
                    first_order_date = datetime.fromisoformat(
                        item["first_order_date"].replace("Z", "+00:00")
                    )
                if item.get("last_order_date"):
                    last_order_date = datetime.fromisoformat(
                        item["last_order_date"].replace("Z", "+00:00")
                    )

                customer_metrics.append(
                    CustomerMetrics(
                        customer_id=item["customer_id"],
                        customer_email=item["customer_email"],
                        total_orders=item["total_orders"],
                        total_spent=Decimal(str(item["total_spent"])),
                        average_order_value=Decimal(str(item["average_order_value"])),
                        first_order_date=first_order_date,
                        last_order_date=last_order_date,
                    )
                )

            return customer_metrics

        except Exception as e:
            raise RuntimeError(f"Failed to get customer metrics: {str(e)}")

    async def get_revenue_summary(
        self, start_date: date, end_date: date
    ) -> Tuple[Decimal, int, Decimal]:
        """Get revenue summary for a period"""
        try:
            query = f"""
                SELECT 
                    SUM(c.total_amount) as total_revenue,
                    COUNT(1) as total_orders,
                    AVG(c.total_amount) as average_order_value
                FROM c 
                WHERE c.type = 'order'
                AND c.created_at >= '{start_date}T00:00:00Z'
                AND c.created_at < '{end_date}T23:59:59Z'
            """

            items = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )

            if items and items[0]:
                item = items[0]
                total_revenue = Decimal(str(item.get("total_revenue", 0)))
                total_orders = item.get("total_orders", 0)
                avg_order_value = Decimal(str(item.get("average_order_value", 0)))
                return total_revenue, total_orders, avg_order_value

            return Decimal("0"), 0, Decimal("0")

        except Exception as e:
            raise RuntimeError(f"Failed to get revenue summary: {str(e)}")

    async def get_busiest_day(
        self, start_date: date, end_date: date
    ) -> Optional[Tuple[date, int]]:
        """Get the day with the highest order count"""
        try:
            query = f"""
                SELECT TOP 1
                    SUBSTRING(c.created_at, 0, 10) as date,
                    COUNT(1) as order_count
                FROM c 
                WHERE c.type = 'order'
                AND c.created_at >= '{start_date}T00:00:00Z'
                AND c.created_at < '{end_date}T23:59:59Z'
                GROUP BY SUBSTRING(c.created_at, 0, 10)
                ORDER BY COUNT(1) DESC
            """

            items = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )

            if items:
                item = items[0]
                busiest_date = datetime.fromisoformat(item["date"]).date()
                order_count = item["order_count"]
                return busiest_date, order_count

            return None

        except Exception as e:
            raise RuntimeError(f"Failed to get busiest day: {str(e)}")

    async def get_highest_revenue_day(
        self, start_date: date, end_date: date
    ) -> Optional[Tuple[date, Decimal]]:
        """Get the day with the highest revenue"""
        try:
            query = f"""
                SELECT TOP 1
                    SUBSTRING(c.created_at, 0, 10) as date,
                    SUM(c.total_amount) as total_revenue
                FROM c 
                WHERE c.type = 'order'
                AND c.created_at >= '{start_date}T00:00:00Z'
                AND c.created_at < '{end_date}T23:59:59Z'
                GROUP BY SUBSTRING(c.created_at, 0, 10)
                ORDER BY SUM(c.total_amount) DESC
            """

            items = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )

            if items:
                item = items[0]
                revenue_date = datetime.fromisoformat(item["date"]).date()
                total_revenue = Decimal(str(item["total_revenue"]))
                return revenue_date, total_revenue

            return None

        except Exception as e:
            raise RuntimeError(f"Failed to get highest revenue day: {str(e)}")
