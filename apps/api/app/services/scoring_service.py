"""
Recovery Scoring Service — Calculates recovery probability.

Abstracted behind a RecoveryScorer interface to allow future
ML model replacement without changing orchestration logic.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models.enums import DiagnosisCode, CaseType
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment


@dataclass
class ScoringFactors:
    """Transparent scoring breakdown for audit trail."""
    failure_reason_score: float
    attempt_penalty: float
    amount_factor: float
    method_factor: float
    recency_factor: float
    final_score: float


class RecoveryScorer(ABC):
    """Abstract scorer interface — swap implementations without coupling."""

    @abstractmethod
    def score(self, case: RecoveryCase, payment: Payment) -> tuple[float, ScoringFactors]:
        """Return (score, factors) where score is 0.0–1.0 recovery probability."""
        ...


class RuleBasedRecoveryScorer(RecoveryScorer):
    """
    Deterministic weighted heuristic scorer.
    
    Uses failure reason, prior attempts, amount, payment method,
    and time since failure to estimate recovery probability.
    """

    # Base recovery probability by diagnosis code
    DIAGNOSIS_WEIGHTS: dict[DiagnosisCode, float] = {
        DiagnosisCode.TRANSIENT_GATEWAY_FAILURE: 0.85,
        DiagnosisCode.CUSTOMER_ACTION_REQUIRED: 0.60,
        DiagnosisCode.PAYMENT_METHOD_FAILURE: 0.40,
        DiagnosisCode.INSUFFICIENT_FUNDS: 0.35,
        DiagnosisCode.EXPIRED_PAYMENT_METHOD: 0.25,
        DiagnosisCode.BANK_DECLINE: 0.30,
        DiagnosisCode.UNKNOWN_PAYMENT_FAILURE: 0.45,
        DiagnosisCode.NON_RECOVERABLE: 0.05,
        DiagnosisCode.ALREADY_RECOVERED: 0.0,
    }

    # Payment method recovery potential
    METHOD_WEIGHTS: dict[str, float] = {
        "card": 1.0,
        "upi": 0.95,
        "netbanking": 0.80,
        "wallet": 0.75,
        "emi": 0.70,
        "bank_transfer": 0.60,
    }

    def score(self, case: RecoveryCase, payment: Payment) -> tuple[float, ScoringFactors]:
        """Calculate deterministic recovery score."""
        # 1. Base score from failure reason (weight: 40%)
        failure_reason_score = self.DIAGNOSIS_WEIGHTS.get(
            case.diagnosis_code, 0.45
        ) if case.diagnosis_code else 0.45

        # 2. Attempt penalty — each retry reduces score (weight: 25%)
        # Score drops 30% per prior attempt
        attempt_penalty = max(0.0, 1.0 - (case.attempt_count * 0.30))

        # 3. Amount factor — very small and very large amounts are harder (weight: 15%)
        amount = payment.amount or 0
        if amount < 1000:  # < ₹10
            amount_factor = 0.5
        elif amount > 5000000:  # > ₹50,000
            amount_factor = 0.7
        else:
            amount_factor = 1.0

        # 4. Payment method factor (weight: 10%)
        method = (payment.method or "").lower()
        method_factor = self.METHOD_WEIGHTS.get(method, 0.80)

        # 5. Recency — fresher failures are more recoverable (weight: 10%)
        # For now, assume all cases are recent (will use timestamps later)
        recency_factor = 1.0

        # Weighted combination
        final_score = (
            failure_reason_score * 0.40
            + attempt_penalty * 0.25
            + amount_factor * 0.15
            + method_factor * 0.10
            + recency_factor * 0.10
        )

        # Clamp to [0, 1]
        final_score = max(0.0, min(1.0, final_score))

        factors = ScoringFactors(
            failure_reason_score=failure_reason_score,
            attempt_penalty=attempt_penalty,
            amount_factor=amount_factor,
            method_factor=method_factor,
            recency_factor=recency_factor,
            final_score=final_score,
        )

        return final_score, factors
