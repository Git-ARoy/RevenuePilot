import uuid
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.simulation.generator import ScenarioGenerator
from app.simulation.batch_runner import BatchRunner
from app.models.merchant import Merchant
from app.models.batch_run import BatchRun
from app.models.recovery_case import RecoveryCase

router = APIRouter(tags=["simulation"])

class GenerateBatchRequest(BaseModel):
    seed: Optional[int] = 42
    count: int = 100
    amount_min: int = 10000
    amount_max: int = 500000
    scenario_mix: Optional[Dict[str, float]] = None

class RunBatchRequest(BaseModel):
    mode: str = 'FULL_AGENT'

async def get_merchant_id(db: AsyncSession) -> uuid.UUID:
    result = await db.execute(select(Merchant).limit(1))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=404, detail="No merchant found")
    return merchant.id

def _serialize_batch(batch: BatchRun) -> dict:
    return {
        "id": str(batch.id),
        "merchant_id": str(batch.merchant_id),
        "mode": batch.mode,
        "seed": batch.seed,
        "config": batch.config,
        "status": batch.status.value if hasattr(batch.status, 'value') else str(batch.status),
        "case_count": batch.case_count,
        "amount_at_risk": batch.amount_at_risk,
        "amount_recovered": batch.amount_recovered,
        "recovery_rate": batch.recovery_rate,
        "metrics": batch.metrics,
        "started_at": batch.started_at.isoformat() if batch.started_at else None,
        "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
    }

@router.post("/generate", response_model=APIResponse)
async def generate_batch(body: GenerateBatchRequest, request: Request, db: AsyncSession = Depends(get_db)):
    merchant_id = await get_merchant_id(db)
    generator = ScenarioGenerator(db, seed=body.seed or 42)
    batch = await generator.generate_batch(
        merchant_id=merchant_id,
        count=body.count,
        amount_min=body.amount_min,
        amount_max=body.amount_max,
        scenario_mix=body.scenario_mix
    )
    await db.commit()
    return APIResponse(
        data={
            "batch_id": str(batch.id),
            "case_count": batch.case_count,
            "amount_at_risk": batch.amount_at_risk,
            "batch": _serialize_batch(batch)
        },
        request_id=request.state.request_id
    )

@router.post("/batches/{batch_id}/run", response_model=APIResponse)
async def run_batch(batch_id: str, body: RunBatchRequest, request: Request, db: AsyncSession = Depends(get_db)):
    b_uuid = uuid.UUID(batch_id)
    runner = BatchRunner(db)
    metrics = await runner.run_batch(batch_id=b_uuid)
    
    # Reload batch
    res = await db.execute(select(BatchRun).where(BatchRun.id == b_uuid))
    batch = res.scalar_one_or_none()
    
    return APIResponse(
        data={
            "batch_id": batch_id,
            "status": batch.status.value if batch and hasattr(batch.status, 'value') else "COMPLETED",
            "metrics": metrics
        },
        request_id=request.state.request_id
    )

@router.get("/batches/{batch_id}", response_model=APIResponse)
async def get_batch(batch_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    b_uuid = uuid.UUID(batch_id)
    res = await db.execute(select(BatchRun).where(BatchRun.id == b_uuid))
    batch = res.scalar_one_or_none()
    if not batch:
        return APIResponse(
            error={"code": "NOT_FOUND", "message": f"Batch {batch_id} not found"},
            request_id=request.state.request_id
        )
    return APIResponse(
        data=_serialize_batch(batch),
        request_id=request.state.request_id
    )

@router.get("/batches", response_model=APIResponse)
async def list_batches(request: Request, db: AsyncSession = Depends(get_db)):
    merchant_id = await get_merchant_id(db)
    res = await db.execute(
        select(BatchRun)
        .where(BatchRun.merchant_id == merchant_id)
        .order_by(BatchRun.created_at.desc())
    )
    batches = res.scalars().all()
    return APIResponse(
        data=[_serialize_batch(b) for b in batches],
        request_id=request.state.request_id
    )
