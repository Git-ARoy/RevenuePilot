"""
Tool Gateway — Central execution point for all recovery actions.

Responsible for:
- Schema validation
- Policy validation (delegates to PolicyEngine)
- Idempotency enforcement
- Action logging
- Timeout handling
- Error normalization
- Routing to appropriate adapter (Razorpay or Simulation)
"""
import uuid
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    ActionType, AttemptStatus, CaseStatus,
    AuditEventType, ActorType
)
from app.models.recovery_case import RecoveryCase
from app.models.recovery_attempt import RecoveryAttempt
from app.models.audit_event import AuditEvent


@dataclass
class ToolRequest:
    """Standardized request to execute a recovery action."""
    case_id: uuid.UUID
    action_type: ActionType
    idempotency_key: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResponse:
    """Standardized response from a recovery action execution."""
    success: bool
    action_type: ActionType
    external_reference: Optional[str] = None  # e.g., plink_xxx
    data: dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retryable: bool = False


class ToolGateway:
    """
    Central tool execution gateway.
    
    All recovery actions pass through here. The gateway enforces
    idempotency, validates requests, logs actions, and routes to
    the appropriate adapter.
    """

    def __init__(self, db: AsyncSession, adapter=None):
        """
        Args:
            db: Database session
            adapter: Recovery action adapter (RazorpayAdapter or SimulationAdapter)
        """
        self.db = db
        self.adapter = adapter

    async def execute(
        self, request: ToolRequest, case: RecoveryCase
    ) -> ToolResponse:
        """
        Execute a recovery action through the gateway.
        
        Steps:
        1. Check idempotency — return cached result if duplicate
        2. Validate request schema
        3. Create recovery attempt record
        4. Execute through adapter
        5. Record result
        6. Create audit events
        """
        # Step 1: Idempotency check
        existing = await self._check_idempotency(request.idempotency_key)
        if existing:
            return self._attempt_to_response(existing)

        # Step 2: Validate
        validation_error = self._validate_request(request)
        if validation_error:
            return ToolResponse(
                success=False,
                action_type=request.action_type,
                error_code="VALIDATION_ERROR",
                error_message=validation_error,
            )

        # Step 3: Create attempt record
        attempt = RecoveryAttempt(
            id=uuid.uuid4(),
            recovery_case_id=request.case_id,
            attempt_number=case.attempt_count + 1,
            action_type=request.action_type,
            status=AttemptStatus.EXECUTING,
            idempotency_key=request.idempotency_key,
            tool_request_hash=self._hash_request(request),
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(attempt)

        # Update case status
        case.status = CaseStatus.ACTION_EXECUTING
        case.attempt_count += 1
        case.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        # Step 4: Execute through adapter
        try:
            response = await self._execute_action(request, case)
        except Exception as e:
            response = ToolResponse(
                success=False,
                action_type=request.action_type,
                error_code="EXECUTION_ERROR",
                error_message=str(e),
                retryable=True,
            )

        # Step 5: Record result
        attempt.status = (
            AttemptStatus.EXECUTED if response.success else AttemptStatus.FAILED
        )
        attempt.tool_response = {
            "success": response.success,
            "external_reference": response.external_reference,
            "data": response.data,
            "error_code": response.error_code,
            "error_message": response.error_message,
        }
        attempt.external_reference = response.external_reference
        attempt.error_code = response.error_code
        attempt.error_description = response.error_message
        attempt.completed_at = datetime.now(timezone.utc)

        # Update case status based on result
        if response.success:
            case.status = CaseStatus.WAITING_FOR_OUTCOME
        else:
            case.status = CaseStatus.ACTION_FAILED
        case.updated_at = datetime.now(timezone.utc)

        # Step 6: Audit events
        audit = AuditEvent(
            id=uuid.uuid4(),
            recovery_case_id=request.case_id,
            event_type=(
                AuditEventType.ACTION_EXECUTED
                if response.success
                else AuditEventType.ACTION_FAILED
            ),
            actor_type=ActorType.AGENT,
            metadata_={
                "action_type": request.action_type.value,
                "attempt_number": attempt.attempt_number,
                "idempotency_key": request.idempotency_key,
                "success": response.success,
                "external_reference": response.external_reference,
                "error_code": response.error_code,
                "error_message": response.error_message,
            },
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(audit)
        await self.db.flush()

        return response

    async def _execute_action(
        self, request: ToolRequest, case: RecoveryCase
    ) -> ToolResponse:
        """Route the action to the appropriate adapter method."""
        if not self.adapter:
            return ToolResponse(
                success=False,
                action_type=request.action_type,
                error_code="NO_ADAPTER",
                error_message="No execution adapter configured.",
            )

        action_map = {
            ActionType.CREATE_PAYMENT_LINK: self.adapter.create_payment_link,
            ActionType.RESEND_PAYMENT_LINK: self.adapter.resend_payment_link,
            ActionType.RETRY_PAYMENT: self.adapter.retry_payment,
            ActionType.SCHEDULE_RETRY: self.adapter.schedule_retry,
        }

        handler = action_map.get(request.action_type)
        if not handler:
            return ToolResponse(
                success=False,
                action_type=request.action_type,
                error_code="UNSUPPORTED_ACTION",
                error_message=f"Action type {request.action_type.value} is not supported by the current adapter.",
            )

        return await handler(case, request.parameters)

    async def _check_idempotency(
        self, idempotency_key: str
    ) -> Optional[RecoveryAttempt]:
        """Check if this idempotency key has been used before."""
        result = await self.db.execute(
            select(RecoveryAttempt).where(
                RecoveryAttempt.idempotency_key == idempotency_key
            )
        )
        return result.scalar_one_or_none()

    def _validate_request(self, request: ToolRequest) -> Optional[str]:
        """Validate the tool request. Returns error message or None."""
        if not request.case_id:
            return "case_id is required"
        if not request.action_type:
            return "action_type is required"
        if not request.idempotency_key:
            return "idempotency_key is required"
        return None

    def _hash_request(self, request: ToolRequest) -> str:
        """Create a deterministic hash of the request for deduplication."""
        payload = json.dumps(
            {
                "case_id": str(request.case_id),
                "action_type": request.action_type.value,
                "parameters": request.parameters,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def _attempt_to_response(self, attempt: RecoveryAttempt) -> ToolResponse:
        """Convert a cached attempt to a ToolResponse."""
        tool_resp = attempt.tool_response or {}
        return ToolResponse(
            success=attempt.status == AttemptStatus.EXECUTED,
            action_type=attempt.action_type,
            external_reference=attempt.external_reference,
            data=tool_resp.get("data", {}),
            error_code=attempt.error_code,
            error_message=attempt.error_description,
        )
