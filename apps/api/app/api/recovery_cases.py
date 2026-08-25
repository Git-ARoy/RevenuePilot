import uuid
from typing import Optional, List, Any
from dataclasses import asdict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, Query, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.common import APIResponse, PaginatedResponse
from app.models.enums import CaseStatus, CaseType, DiagnosisCode, ActionType, AuditEventType, ActorType
from app.models.merchant import Merchant
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.audit_event import AuditEvent
from app.services.case_service import CaseService
from app.services.audit_service import AuditService
from app.services.diagnosis_service import DiagnosisService
from app.services.scoring_service import RuleBasedRecoveryScorer
from app.policies.policy_engine import PolicyEngine
from app.services.strategy_service import StrategyService
from app.services.orchestrator import RecoveryOrchestrator

router = APIRouter(tags=["recovery-cases"])

class ActionRequest(BaseModel):
    action_type: ActionType
    reason_code: Optional[str] = None

class EscalateRequest(BaseModel):
    reason_code: str
    notes: Optional[str] = None

async def get_merchant_id(db: AsyncSession) -> uuid.UUID:
    result = await db.execute(select(Merchant).limit(1))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=404, detail="No merchant found")
    return merchant.id

def _serialize_case(case: RecoveryCase) -> dict:
    return {
        "id": str(case.id),
        "merchant_id": str(case.merchant_id),
        "payment_id": str(case.payment_id) if case.payment_id else None,
        "batch_id": str(case.batch_id) if case.batch_id else None,
        "case_type": case.case_type.value if hasattr(case.case_type, 'value') else str(case.case_type),
        "amount_at_risk": case.amount_at_risk,
        "amount_recovered": case.amount_recovered,
        "currency": case.currency,
        "status": case.status.value if hasattr(case.status, 'value') else str(case.status),
        "diagnosis_code": case.diagnosis_code.value if hasattr(case.diagnosis_code, 'value') else (str(case.diagnosis_code) if case.diagnosis_code else None),
        "diagnosis_confidence": case.diagnosis_confidence,
        "recovery_score": case.recovery_score,
        "current_strategy": case.current_strategy.value if hasattr(case.current_strategy, 'value') else (str(case.current_strategy) if case.current_strategy else None),
        "attempt_count": case.attempt_count,
        "max_attempts": case.max_attempts,
        "next_eligible_at": case.next_eligible_at.isoformat() if case.next_eligible_at else None,
        "terminal_reason": case.terminal_reason,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
    }

def _serialize_audit(event: AuditEvent) -> dict:
    return {
        "id": str(event.id),
        "recovery_case_id": str(event.recovery_case_id) if event.recovery_case_id else None,
        "event_type": event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
        "actor_type": event.actor_type.value if hasattr(event.actor_type, 'value') else str(event.actor_type),
        "actor_id": event.actor_id,
        "metadata": event.metadata_,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }

@router.get("", response_model=APIResponse)
@router.get("/", response_model=APIResponse)
async def list_cases(
    request: Request,
    status: Optional[CaseStatus] = None,
    case_type: Optional[CaseType] = None,
    diagnosis_code: Optional[DiagnosisCode] = None,
    batch_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    merchant_id = await get_merchant_id(db)
    case_service = CaseService(db)
    
    b_uuid = uuid.UUID(batch_id) if batch_id else None
    cases, total = await case_service.list_cases(
        merchant_id=merchant_id,
        status=status,
        case_type=case_type,
        diagnosis_code=diagnosis_code,
        batch_id=b_uuid,
        page=page,
        page_size=page_size
    )
    
    serialized_cases = [_serialize_case(c) for c in cases]
    
    return APIResponse(
        data={
            "items": serialized_cases,
            "page": page,
            "page_size": page_size,
            "total": total
        },
        request_id=request.state.request_id
    )

@router.get("/{case_id}", response_model=APIResponse)
async def get_case(case_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    case_service = CaseService(db)
    audit_service = AuditService(db)
    
    c_uuid = uuid.UUID(case_id)
    case_obj = await case_service.get_case(c_uuid)
    if not case_obj:
        return APIResponse(
            error={"code": "NOT_FOUND", "message": f"Case {case_id} not found"},
            request_id=request.state.request_id
        )
        
    timeline = await audit_service.get_timeline(c_uuid)
    
    return APIResponse(
        data={
            "case": _serialize_case(case_obj),
            "timeline": [_serialize_audit(ev) for ev in timeline]
        },
        request_id=request.state.request_id
    )

@router.post("/{case_id}/evaluate", response_model=APIResponse)
async def evaluate_case(case_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    c_uuid = uuid.UUID(case_id)
    case_service = CaseService(db)
    case_obj = await case_service.get_case(c_uuid)
    if not case_obj:
        return APIResponse(
            error={"code": "NOT_FOUND", "message": f"Case {case_id} not found"},
            request_id=request.state.request_id
        )
        
    payment = (await db.execute(select(Payment).where(Payment.id == case_obj.payment_id))).scalar_one_or_none()
    
    diagnosis_service = DiagnosisService(db)
    policy_engine = PolicyEngine(db)
    strategy_service = StrategyService(db)
    scorer = RuleBasedRecoveryScorer()
    
    diagnosis = await diagnosis_service.diagnose(case_obj, payment)
    score, _ = scorer.score(case_obj, payment)
    strategy = await strategy_service.select_strategy(case_obj, payment, score)
    policy_decision = await policy_engine.evaluate(case_obj, strategy.action_type)
    
    return APIResponse(
        data={
            "case_id": case_id,
            "diagnosis": {
                "code": diagnosis.code.value,
                "confidence": diagnosis.confidence,
                "reason": diagnosis.reason
            },
            "candidate_action": {
                "type": strategy.action_type.value,
                "reason_code": strategy.reason_code,
                "confidence": strategy.confidence
            },
            "policy": {
                "allowed": policy_decision.allowed,
                "checks": [{"rule": c.rule, "passed": c.passed, "detail": c.detail} for c in policy_decision.checks],
                "block_reason": policy_decision.block_reason
            }
        },
        request_id=request.state.request_id
    )

@router.post("/{case_id}/actions", response_model=APIResponse)
async def execute_action(
    case_id: str,
    body: ActionRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db)
):
    c_uuid = uuid.UUID(case_id)
    orchestrator = RecoveryOrchestrator(db)
    case_obj = await orchestrator.process_case(
        case_id=c_uuid,
        action_type=body.action_type,
        reason_code=body.reason_code,
        idempotency_key=idempotency_key
    )
    
    if not case_obj:
        return APIResponse(
            error={"code": "NOT_FOUND", "message": f"Case {case_id} not found"},
            request_id=request.state.request_id
        )
        
    return APIResponse(
        data=_serialize_case(case_obj),
        request_id=request.state.request_id
    )

@router.post("/{case_id}/escalate", response_model=APIResponse)
async def escalate_case(
    case_id: str,
    body: EscalateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    c_uuid = uuid.UUID(case_id)
    case_service = CaseService(db)
    case_obj = await case_service.get_case(c_uuid)
    if not case_obj:
        return APIResponse(
            error={"code": "NOT_FOUND", "message": f"Case {case_id} not found"},
            request_id=request.state.request_id
        )
        
    case_obj.status = CaseStatus.ESCALATED
    case_obj.terminal_reason = f"Manual Escalation: {body.reason_code} - {body.notes or ''}"
    case_obj.updated_at = datetime.now(timezone.utc)
    
    audit = AuditEvent(
        id=uuid.uuid4(),
        recovery_case_id=case_obj.id,
        event_type=AuditEventType.CASE_ESCALATED,
        actor_type=ActorType.MERCHANT,
        metadata_={"reason_code": body.reason_code, "notes": body.notes},
        created_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    await db.commit()
    
    return APIResponse(
        data=_serialize_case(case_obj),
        request_id=request.state.request_id
    )

@router.get("/{case_id}/audit", response_model=APIResponse)
async def get_audit(case_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    c_uuid = uuid.UUID(case_id)
    audit_service = AuditService(db)
    timeline = await audit_service.get_timeline(c_uuid)
    
    return APIResponse(
        data={"events": [_serialize_audit(ev) for ev in timeline]},
        request_id=request.state.request_id
    )
