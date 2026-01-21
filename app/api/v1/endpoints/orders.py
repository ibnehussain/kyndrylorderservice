"""Order API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse, MessageResponse
)
from app.services.order_service import OrderService, get_order_service
from app.models.base import OrderStatus

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description="Create a new order with customer, items, and payment information"
)
async def create_order(
    order_data: OrderCreate,
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """Create a new order"""
    try:
        order = await order_service.create_order(order_data)
        return OrderResponse(**order.dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create order: {str(e)}"
        )


@router.get(
    "/",
    response_model=OrderListResponse,
    summary="List orders with pagination",
    description="Get a paginated list of orders, optionally filtered by customer or status"
)
async def list_orders(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    order_status: Optional[OrderStatus] = Query(None, alias="status", description="Filter by order status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    order_service: OrderService = Depends(get_order_service)
) -> OrderListResponse:
    """List orders with pagination and optional filters"""
    try:
        orders, total_count = await order_service.list_orders(
            customer_id=customer_id,
            status=order_status,
            page=page,
            page_size=page_size
        )
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return OrderListResponse(
            orders=[OrderResponse(**order.dict()) for order in orders],
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list orders: {str(e)}"
        )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID",
    description="Retrieve a specific order by its ID and customer ID"
)
async def get_order(
    order_id: str,
    customer_id: str = Query(..., description="Customer ID for the order"),
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """Get a specific order by ID"""
    try:
        order = await order_service.get_order(order_id, customer_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )
        return OrderResponse(**order.dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order: {str(e)}"
        )


@router.get(
    "/number/{order_number}",
    response_model=OrderResponse,
    summary="Get order by order number",
    description="Retrieve a specific order by its order number"
)
async def get_order_by_number(
    order_number: str,
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """Get a specific order by order number"""
    try:
        order = await order_service.get_order_by_number(order_number)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_number} not found"
            )
        return OrderResponse(**order.dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order: {str(e)}"
        )


@router.put(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Update order",
    description="Update an existing order's status, notes, or shipping address"
)
async def update_order(
    order_id: str,
    customer_id: str = Query(..., description="Customer ID for the order"),
    update_data: OrderUpdate = ...,
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """Update an existing order"""
    try:
        order = await order_service.update_order(order_id, customer_id, update_data)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )
        return OrderResponse(**order.dict())
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update order: {str(e)}"
        )


@router.post(
    "/{order_id}/cancel",
    response_model=MessageResponse,
    summary="Cancel order",
    description="Cancel an existing order if it's in a cancellable state"
)
async def cancel_order(
    order_id: str,
    customer_id: str = Query(..., description="Customer ID for the order"),
    order_service: OrderService = Depends(get_order_service)
) -> MessageResponse:
    """Cancel an existing order"""
    try:
        order = await order_service.cancel_order(order_id, customer_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )
        return MessageResponse(
            message=f"Order {order.order_number} cancelled successfully",
            order_id=order.id
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel order: {str(e)}"
        )


@router.delete(
    "/{order_id}",
    response_model=MessageResponse,
    summary="Delete order",
    description="Permanently delete an order (admin operation)"
)
async def delete_order(
    order_id: str,
    customer_id: str = Query(..., description="Customer ID for the order"),
    order_service: OrderService = Depends(get_order_service)
) -> MessageResponse:
    """Delete an order (admin operation)"""
    try:
        deleted = await order_service.delete_order(order_id, customer_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )
        return MessageResponse(
            message=f"Order {order_id} deleted successfully",
            order_id=order_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete order: {str(e)}"
        )


@router.get(
    "/customers/{customer_id}/orders",
    response_model=OrderListResponse,
    summary="Get customer orders",
    description="Get all orders for a specific customer with pagination"
)
async def get_customer_orders(
    customer_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    order_service: OrderService = Depends(get_order_service)
) -> OrderListResponse:
    """Get all orders for a specific customer"""
    try:
        orders, total_count = await order_service.get_customer_orders(
            customer_id=customer_id,
            page=page,
            page_size=page_size
        )
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return OrderListResponse(
            orders=[OrderResponse(**order.dict()) for order in orders],
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer orders: {str(e)}"
        )