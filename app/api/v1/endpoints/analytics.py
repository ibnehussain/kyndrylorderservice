"""Analytics API endpoints for order metrics and reporting"""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.analytics import CustomerMetrics
from app.schemas.analytics import (
    AnalyticsDateRange,
    AnalyticsQueryParams,
    AnalyticsSummaryResponse,
    DailyAnalyticsResponse,
    OrderStatusAnalyticsResponse,
    TopCustomersResponse,
)
from app.services.analytics_service import AnalyticsService, get_analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/daily",
    response_model=DailyAnalyticsResponse,
    summary="Get daily order analytics",
    description="Retrieve daily order metrics including revenue, order count, and average order value for a specified date range",
)
async def get_daily_analytics(
    start_date: Optional[date] = Query(
        None, description="Start date (YYYY-MM-DD). Defaults to 30 days ago"
    ),
    end_date: Optional[date] = Query(
        None, description="End date (YYYY-MM-DD). Defaults to today"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> DailyAnalyticsResponse:
    """Get daily analytics metrics"""
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=29)  # 30 days total

        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before or equal to end date",
            )

        if end_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date cannot be in the future",
            )

        date_range = AnalyticsDateRange(start_date=start_date, end_date=end_date)
        return await analytics_service.get_daily_analytics(date_range)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily analytics: {str(e)}",
        )


@router.get(
    "/orders/status",
    response_model=OrderStatusAnalyticsResponse,
    summary="Get order analytics by status",
    description="Retrieve order metrics grouped by order status (pending, confirmed, shipped, etc.)",
)
async def get_order_status_analytics(
    start_date: Optional[date] = Query(
        None, description="Start date (YYYY-MM-DD). Defaults to 30 days ago"
    ),
    end_date: Optional[date] = Query(
        None, description="End date (YYYY-MM-DD). Defaults to today"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> OrderStatusAnalyticsResponse:
    """Get order analytics grouped by status"""
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=29)

        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before or equal to end date",
            )

        date_range = AnalyticsDateRange(start_date=start_date, end_date=end_date)
        return await analytics_service.get_order_status_analytics(date_range)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order status analytics: {str(e)}",
        )


@router.get(
    "/customers/top",
    response_model=TopCustomersResponse,
    summary="Get top customers analytics",
    description="Retrieve top customers ranked by total spending amount",
)
async def get_top_customers_analytics(
    start_date: Optional[date] = Query(
        None, description="Start date (YYYY-MM-DD). Defaults to 30 days ago"
    ),
    end_date: Optional[date] = Query(
        None, description="End date (YYYY-MM-DD). Defaults to today"
    ),
    limit: int = Query(
        default=10, ge=1, le=100, description="Maximum number of customers to return"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> TopCustomersResponse:
    """Get top customers by spending"""
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=29)

        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before or equal to end date",
            )

        date_range = AnalyticsDateRange(start_date=start_date, end_date=end_date)
        return await analytics_service.get_top_customers(date_range, limit)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get top customers analytics: {str(e)}",
        )


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
    summary="Get comprehensive analytics summary",
    description="Retrieve a comprehensive analytics dashboard with revenue, trends, top customers, and key insights",
)
async def get_analytics_summary(
    start_date: Optional[date] = Query(
        None, description="Start date (YYYY-MM-DD). Defaults to current month start"
    ),
    end_date: Optional[date] = Query(
        None, description="End date (YYYY-MM-DD). Defaults to today"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsSummaryResponse:
    """Get comprehensive analytics summary"""
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            # Default to current month
            start_date = end_date.replace(day=1)

        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before or equal to end date",
            )

        date_range = AnalyticsDateRange(start_date=start_date, end_date=end_date)
        return await analytics_service.get_analytics_summary(date_range)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics summary: {str(e)}",
        )


@router.get(
    "/revenue/trends",
    response_model=DailyAnalyticsResponse,
    summary="Get revenue trends",
    description="Retrieve revenue trends for the specified number of days",
)
async def get_revenue_trends(
    days: int = Query(
        default=30, ge=1, le=365, description="Number of days to analyze"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> DailyAnalyticsResponse:
    """Get revenue trends for the last N days"""
    try:
        return await analytics_service.get_revenue_trends(days)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get revenue trends: {str(e)}",
        )


@router.get(
    "/customers/{customer_id}",
    response_model=CustomerMetrics,
    summary="Get customer analytics",
    description="Retrieve detailed analytics for a specific customer",
)
async def get_customer_analytics(
    customer_id: str,
    start_date: Optional[date] = Query(
        None, description="Start date (YYYY-MM-DD). Defaults to 1 year ago"
    ),
    end_date: Optional[date] = Query(
        None, description="End date (YYYY-MM-DD). Defaults to today"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> CustomerMetrics:
    """Get analytics for a specific customer"""
    try:
        date_range = None
        if start_date or end_date:
            # Set default date range if not provided
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date.replace(year=end_date.year - 1)  # 1 year ago

            # Validate date range
            if start_date > end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Start date must be before or equal to end date",
                )

            date_range = AnalyticsDateRange(start_date=start_date, end_date=end_date)

        return await analytics_service.get_customer_analytics(customer_id, date_range)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer analytics: {str(e)}",
        )


# Additional convenience endpoints


@router.get(
    "/quick/today",
    response_model=DailyAnalyticsResponse,
    summary="Get today's analytics",
    description="Retrieve analytics for today only",
)
async def get_today_analytics(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> DailyAnalyticsResponse:
    """Get analytics for today"""
    today = date.today()
    date_range = AnalyticsDateRange(start_date=today, end_date=today)
    return await analytics_service.get_daily_analytics(date_range)


@router.get(
    "/quick/week",
    response_model=DailyAnalyticsResponse,
    summary="Get this week's analytics",
    description="Retrieve analytics for the last 7 days",
)
async def get_week_analytics(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> DailyAnalyticsResponse:
    """Get analytics for the last 7 days"""
    return await analytics_service.get_revenue_trends(days=7)


@router.get(
    "/quick/month",
    response_model=AnalyticsSummaryResponse,
    summary="Get this month's analytics summary",
    description="Retrieve comprehensive analytics for the current month",
)
async def get_month_analytics_summary(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsSummaryResponse:
    """Get analytics summary for current month"""
    today = date.today()
    start_of_month = today.replace(day=1)
    date_range = AnalyticsDateRange(start_date=start_of_month, end_date=today)
    return await analytics_service.get_analytics_summary(date_range)
