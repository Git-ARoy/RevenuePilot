"""
Simulation Adapter — Same interface as RazorpayAdapter for simulation mode.

Produces deterministic outcomes based on scenario configuration.
The orchestration layer cannot tell the difference between this
and the real Razorpay adapter.
"""
import uuid
from typing import Any

from app.models.recovery_case import RecoveryCase
from app.models.enums import ActionType, DiagnosisCode
from app.integrations.tool_gateway import ToolResponse


class SimulationAdapter:
    """
    Simulates Razorpay API responses for batch evaluation.
    
    Recovery success rates vary by diagnosis code to produce
    realistic batch metrics.
    """

    # Simulated success rates by diagnosis code
    SUCCESS_RATES: dict[DiagnosisCode, float] = {
        DiagnosisCode.TRANSIENT_GATEWAY_FAILURE: 0.80,
        DiagnosisCode.CUSTOMER_ACTION_REQUIRED: 0.55,
        DiagnosisCode.PAYMENT_METHOD_FAILURE: 0.35,
        DiagnosisCode.INSUFFICIENT_FUNDS: 0.25,
        DiagnosisCode.EXPIRED_PAYMENT_METHOD: 0.20,
        DiagnosisCode.BANK_DECLINE: 0.30,
        DiagnosisCode.UNKNOWN_PAYMENT_FAILURE: 0.40,
        DiagnosisCode.NON_RECOVERABLE: 0.0,
        DiagnosisCode.ALREADY_RECOVERED: 0.0,
    }

    def __init__(self, seed: int = 42, inject_failures: bool = False):
        import random
        self.rng = random.Random(seed)
        self.inject_failures = inject_failures
        self._call_count = 0

    def _should_succeed(self, case: RecoveryCase) -> bool:
        """Deterministic success decision based on diagnosis and RNG."""
        # Inject tool/API failures at 5% rate for demonstrating failure handling
        if self.inject_failures:
            self._call_count += 1
            if self._call_count % 20 == 0:  # Every 20th call fails
                return False

        rate = self.SUCCESS_RATES.get(
            case.diagnosis_code, 0.40
        )

        # Reduce success rate with each attempt
        adjusted_rate = rate * (0.7 ** case.attempt_count)

        return self.rng.random() < adjusted_rate

    async def create_payment_link(
        self, case: RecoveryCase, params: dict[str, Any]
    ) -> ToolResponse:
        """Simulate creating a payment link."""
        # Simulate occasional API failures
        if self.inject_failures and self.rng.random() < 0.05:
            return ToolResponse(
                success=False,
                action_type=ActionType.CREATE_PAYMENT_LINK,
                error_code="SIMULATED_API_ERROR",
                error_message="Simulated Razorpay API failure for testing.",
                retryable=True,
            )

        sim_link_id = f"plink_sim_{uuid.uuid4().hex[:12]}"
        success = self._should_succeed(case)

        return ToolResponse(
            success=True,  # Link creation succeeds (payment may not)
            action_type=ActionType.CREATE_PAYMENT_LINK,
            external_reference=sim_link_id,
            data={
                "short_url": f"https://rzp.io/sim/{sim_link_id[-8:]}",
                "status": "created",
                "amount": case.amount_at_risk,
                "will_be_paid": success,  # Simulation-only flag for outcome resolution
                "razorpay_link_id": sim_link_id,
            },
        )

    async def resend_payment_link(
        self, case: RecoveryCase, params: dict[str, Any]
    ) -> ToolResponse:
        """Simulate resending a payment link."""
        return ToolResponse(
            success=True,
            action_type=ActionType.RESEND_PAYMENT_LINK,
            external_reference=params.get("payment_link_id", "plink_sim_unknown"),
            data={"medium": params.get("medium", "sms"), "simulated": True},
        )

    async def retry_payment(
        self, case: RecoveryCase, params: dict[str, Any]
    ) -> ToolResponse:
        """Simulate retrying a payment (implemented as new payment link)."""
        return await self.create_payment_link(case, params)

    async def schedule_retry(
        self, case: RecoveryCase, params: dict[str, Any]
    ) -> ToolResponse:
        """Simulate scheduling a delayed retry."""
        return await self.create_payment_link(case, params)
