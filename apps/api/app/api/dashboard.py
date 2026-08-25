from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dataclasses import asdict
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.services.metrics_service import MetricsService
from app.models.merchant import Merchant

router = APIRouter(tags=["dashboard"])

@router.get("/summary", response_model=APIResponse)
async def get_dashboard_summary(request: Request, db: AsyncSession = Depends(get_db)):
    metrics_service = MetricsService(db)
    
    result = await db.execute(select(Merchant).limit(1))
    merchant = result.scalar_one_or_none()
    
    if not merchant:
        return APIResponse(
            error={"code": "NOT_FOUND", "message": "No merchant found"},
            request_id=request.state.request_id
        )
        
    summary = await metrics_service.get_dashboard_summary(merchant.id)
    data = asdict(summary)
    
    # Add period metadata
    now = datetime.now(timezone.utc)
    data["period"] = {
        "from": (now - timedelta(days=30)).isoformat(),
        "to": now.isoformat()
    }
    
    return APIResponse(
        data=data,
        request_id=request.state.request_id
    )
