import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.policies.policy_engine import PolicyEngine
from app.models.enums import ActionType, AuditEventType, ActorType
from app.models.merchant import Merchant
from app.models.policy_config import PolicyConfig
from app.models.audit_event import AuditEvent
from datetime import datetime, timezone

router = APIRouter(tags=["policies"])

class PolicyUpdateRequest(BaseModel):
    max_attempts: int = Field(..., ge=0)
    retry_cooldown_seconds: int = Field(..., ge=0)
    max_automated_recovery_amount: int = Field(..., ge=0)
    human_approval_threshold: int = Field(..., ge=0)
    allowed_actions: List[str]

async def get_merchant_id(db: AsyncSession) -> uuid.UUID:
    result = await db.execute(select(Merchant).limit(1))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=404, detail="No merchant found")
    return merchant.id

def _serialize_policy(policy: PolicyConfig) -> dict:
    return {
        "id": str(policy.id),
        "merchant_id": str(policy.merchant_id),
        "max_attempts": policy.max_attempts,
        "retry_cooldown_seconds": policy.retry_cooldown_seconds,
        "max_automated_recovery_amount": policy.max_automated_recovery_amount,
        "human_approval_threshold": policy.human_approval_threshold,
        "allowed_actions": policy.allowed_actions,
        "escalation_threshold": policy.escalation_threshold,
        "model_selection": policy.model_selection,
        "simulation_mode": policy.simulation_mode,
        "created_at": policy.created_at.isoformat() if policy.created_at else None,
        "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
    }

@router.get("", response_model=APIResponse)
@router.get("/", response_model=APIResponse)
async def get_policy(request: Request, db: AsyncSession = Depends(get_db)):
    merchant_id = await get_merchant_id(db)
    policy_engine = PolicyEngine(db)
    policy = await policy_engine.get_policy(merchant_id)
    return APIResponse(
        data=_serialize_policy(policy),
        request_id=request.state.request_id
    )

@router.put("", response_model=APIResponse)
@router.put("/", response_model=APIResponse)
async def update_policy(body: PolicyUpdateRequest, request: Request, db: AsyncSession = Depends(get_db)):
    merchant_id = await get_merchant_id(db)
    policy_engine = PolicyEngine(db)
    policy = await policy_engine.get_policy(merchant_id)
    
    policy.max_attempts = body.max_attempts
    policy.retry_cooldown_seconds = body.retry_cooldown_seconds
    policy.max_automated_recovery_amount = body.max_automated_recovery_amount
    policy.human_approval_threshold = body.human_approval_threshold
    policy.allowed_actions = body.allowed_actions
    policy.updated_at = datetime.now(timezone.utc)
    
    audit = AuditEvent(
        id=uuid.uuid4(),
        event_type=AuditEventType.POLICY_UPDATED,
        actor_type=ActorType.MERCHANT,
        metadata_={
            "max_attempts": body.max_attempts,
            "retry_cooldown_seconds": body.retry_cooldown_seconds,
            "max_automated_recovery_amount": body.max_automated_recovery_amount,
            "human_approval_threshold": body.human_approval_threshold,
            "allowed_actions": body.allowed_actions
        },
        created_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    await db.commit()
    
    return APIResponse(
        data=_serialize_policy(policy),
        request_id=request.state.request_id
    )
