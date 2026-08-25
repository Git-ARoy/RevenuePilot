"""
Diagnosis Service — Failure classification and root cause analysis.

Uses deterministic Razorpay error codes first, falls back to LLM
for ambiguous failure descriptions.
"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    DiagnosisCode, AuditEventType, ActorType, CaseStatus
)
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.agent_decision import AgentDecision
from app.models.audit_event import AuditEvent


@dataclass
class DiagnosisResult:
    """Structured diagnosis output."""
    code: DiagnosisCode
    confidence: float  # 0.0 to 1.0
    reason: str
    used_llm: bool = False


# Deterministic mapping from Razorpay error codes to diagnosis codes.
# These are evaluated BEFORE any LLM call.
ERROR_CODE_MAP: dict[str, DiagnosisCode] = {
    "BAD_REQUEST_ERROR": DiagnosisCode.TRANSIENT_GATEWAY_FAILURE,
    "GATEWAY_ERROR": DiagnosisCode.TRANSIENT_GATEWAY_FAILURE,
    "SERVER_ERROR": DiagnosisCode.TRANSIENT_GATEWAY_FAILURE,
    "PAYMENT_FAILED": DiagnosisCode.UNKNOWN_PAYMENT_FAILURE,
}

# Keyword-based classification from error descriptions.
# Evaluated in order — first match wins.
DESCRIPTION_RULES: list[tuple[list[str], DiagnosisCode, str]] = [
    (
        ["insufficient", "balance", "low balance", "not enough"],
        DiagnosisCode.INSUFFICIENT_FUNDS,
        "Payment failed due to insufficient funds in customer account.",
    ),
    (
        ["expired", "card expired", "validity"],
        DiagnosisCode.EXPIRED_PAYMENT_METHOD,
        "Payment method has expired.",
    ),
    (
        ["declined", "bank decline", "issuer decline", "do not honour", "do not honor"],
        DiagnosisCode.BANK_DECLINE,
        "Payment was declined by the issuing bank.",
    ),
    (
        ["invalid card", "incorrect cvv", "invalid cvv", "card number", "invalid account"],
        DiagnosisCode.PAYMENT_METHOD_FAILURE,
        "Payment method details are invalid or incorrect.",
    ),
    (
        ["otp", "authentication", "3ds", "3d secure", "customer action", "verification"],
        DiagnosisCode.CUSTOMER_ACTION_REQUIRED,
        "Customer action (e.g., OTP/3DS verification) is required to complete payment.",
    ),
    (
        ["timeout", "timed out", "gateway timeout", "network error", "connection"],
        DiagnosisCode.TRANSIENT_GATEWAY_FAILURE,
        "Transient gateway or network failure. Retry is likely to succeed.",
    ),
    (
        ["fraud", "risk", "blocked", "blacklist", "suspicious"],
        DiagnosisCode.NON_RECOVERABLE,
        "Payment blocked due to risk/fraud controls. Not recoverable.",
    ),
    (
        ["refund", "already paid", "duplicate", "already captured"],
        DiagnosisCode.ALREADY_RECOVERED,
        "Payment has already been processed or recovered.",
    ),
]


class DiagnosisService:
    """Classifies payment failures into actionable diagnosis categories."""

    def __init__(self, db: AsyncSession, llm_provider=None):
        self.db = db
        self.llm_provider = llm_provider

    async def diagnose(
        self, case: RecoveryCase, payment: Payment
    ) -> DiagnosisResult:
        """
        Diagnose a recovery case.
        
        Strategy:
        1. Try deterministic error code mapping
        2. Try keyword-based description matching
        3. Fall back to LLM for ambiguous cases (if available)
        4. Default to UNKNOWN_PAYMENT_FAILURE
        """
        # Step 1: Deterministic error code mapping
        result = self._diagnose_from_error_code(payment)
        if result and result.confidence >= 0.8:
            await self._persist_diagnosis(case, result, payment)
            return result

        # Step 2: Keyword-based description matching
        desc_result = self._diagnose_from_description(payment)
        if desc_result:
            # If we got a moderate-confidence code result too, pick the better one
            if result and result.confidence > desc_result.confidence:
                await self._persist_diagnosis(case, result, payment)
                return result
            await self._persist_diagnosis(case, desc_result, payment)
            return desc_result

        # Step 3: LLM fallback for ambiguous cases
        if self.llm_provider and payment.error_description:
            llm_result = await self._diagnose_with_llm(payment)
            if llm_result:
                await self._persist_diagnosis(case, llm_result, payment)
                return llm_result

        # Step 4: Default
        fallback = DiagnosisResult(
            code=DiagnosisCode.UNKNOWN_PAYMENT_FAILURE,
            confidence=0.3,
            reason="Unable to determine specific failure cause from available data.",
        )
        if result:  # Use partial error code match if available
            fallback = result
        await self._persist_diagnosis(case, fallback, payment)
        return fallback

    def _diagnose_from_error_code(
        self, payment: Payment
    ) -> Optional[DiagnosisResult]:
        """Map Razorpay error codes to diagnosis codes deterministically."""
        if not payment.error_code:
            return None

        code_upper = payment.error_code.upper()

        # Direct map lookup
        if code_upper in ERROR_CODE_MAP:
            return DiagnosisResult(
                code=ERROR_CODE_MAP[code_upper],
                confidence=0.75,
                reason=f"Determined from error code: {payment.error_code}",
            )

        return None

    def _diagnose_from_description(
        self, payment: Payment
    ) -> Optional[DiagnosisResult]:
        """Match error description keywords to diagnosis codes."""
        if not payment.error_description:
            return None

        desc_lower = payment.error_description.lower()

        for keywords, diagnosis_code, reason in DESCRIPTION_RULES:
            for keyword in keywords:
                if keyword in desc_lower:
                    return DiagnosisResult(
                        code=diagnosis_code,
                        confidence=0.85,
                        reason=reason,
                    )

        return None

    async def _diagnose_with_llm(
        self, payment: Payment
    ) -> Optional[DiagnosisResult]:
        """Use LLM to classify ambiguous failure descriptions."""
        if not self.llm_provider:
            return None

        try:
            evidence = {
                "payment_status": payment.status,
                "amount": payment.amount,
                "error_code": payment.error_code,
                "error_description": payment.error_description,
                "method": payment.method,
            }

            llm_result = await self.llm_provider.diagnose(evidence)
            if llm_result and "code" in llm_result:
                try:
                    code = DiagnosisCode(llm_result["code"])
                    return DiagnosisResult(
                        code=code,
                        confidence=min(float(llm_result.get("confidence", 0.6)), 0.9),
                        reason=llm_result.get("reason", "Classified by AI model."),
                        used_llm=True,
                    )
                except (ValueError, KeyError):
                    pass
        except Exception:
            # LLM failures are non-fatal — fall through to default
            pass

        return None

    async def _persist_diagnosis(
        self,
        case: RecoveryCase,
        result: DiagnosisResult,
        payment: Payment,
    ) -> None:
        """Persist diagnosis result to case and create audit trail."""
        case.diagnosis_code = result.code
        case.diagnosis_confidence = result.confidence
        case.status = CaseStatus.DIAGNOSED
        case.updated_at = datetime.now(timezone.utc)

        # Record agent decision
        decision = AgentDecision(
            id=uuid.uuid4(),
            recovery_case_id=case.id,
            stage="diagnosis",
            decision=result.code.value,
            reason_code=result.reason[:200],
            evidence={
                "payment_status": payment.status,
                "error_code": payment.error_code,
                "error_description": payment.error_description,
                "method": payment.method,
            },
            model_provider=self.llm_provider.__class__.__name__ if result.used_llm else None,
            model_name=None,
            confidence=result.confidence,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(decision)

        # Audit event
        audit = AuditEvent(
            id=uuid.uuid4(),
            recovery_case_id=case.id,
            event_type=AuditEventType.CASE_DIAGNOSED,
            actor_type=ActorType.AGENT,
            metadata_={
                "diagnosis_code": result.code.value,
                "confidence": result.confidence,
                "reason": result.reason,
                "used_llm": result.used_llm,
            },
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(audit)
        await self.db.flush()
