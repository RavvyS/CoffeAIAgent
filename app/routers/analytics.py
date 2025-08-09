# app/routers/analytics.py
# TODO: Copy content from "Analytics API Routes" artifact
from fastapi import APIRouter, Query
from datetime import datetime

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard")
async def get_dashboard_metrics(days: int = Query(7, ge=1, le=30)):
    """Get dashboard metrics - placeholder"""
    return {
        "success": True,
        "data": {"overview": {"total_conversations": 100}},
        "period": f"Last {days} days"
    }
