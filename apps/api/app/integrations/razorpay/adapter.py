"""
Razorpay Adapter — Bridges the tool gateway to Razorpay API.

Same interface as SimulationAdapter so the orchestration layer
can swap between real Razorpay and simulation without changes.
"""
import uuid
from typing import Any

from app.models.recovery_case import RecoveryCase
from app.models.enums import ActionType
from app.integrations.tool_gateway import ToolResponse
from app.integrations.razorpay.client import RazorpayClient, RazorpayAPIError


class RazorpayAdapter:
    """
    Adapter that translates recovery actions into Razorpay API calls.
    
    Implements the same interface as SimulationAdapter.
    """

    def __init__(self, client: RazorpayClient | None = None):
        self.client = client or RazorpayClient()

    async def create_payment_link(
        self, case: RecoveryCase, params: dict[str, Any]
    ) -> ToolResponse:
        """Create a Razorpay Payment Link for recovery."""
        try:
            result = await self.client.create_payment_link(
                amount=case.amount_at_risk,
                currency=case.currency,
                description=f"Recovery payment for order (Case: {str(case.id)[:8]})",
                customer=params.get("customer"),
                notify={"sms": True, "email": True},
                reminder_enable=True,
                notes={
                    "recovery_case_id": str(case.id),
                    "original_payment_id": str(case.payment_id),
                    "source": "revenuepilot",
                },
                expire_by=params.get("expire_by"),
            )

            return ToolResponse(
                success=True,
                action_type=ActionType.CREATE_PAYMENT_LINK,
                external_reference=result.get("id"),
                data={
                    "short_url": result.get("short_url"),
                    "status": result.get("status"),
                    "amount": result.get("amount"),
                    "razorpay_link_id": result.get("id"),
                },
            )

        except RazorpayAPIError as e:
            return ToolResponse(
                success=False,
                action_type=ActionType.CREATE_PAYMENT_LINK,
                error_code=e.error.code,
                error_message=e.error.description,
                retryable=e.error.status_code >= 500,
            )
        except Exception as e:
            return ToolResponse(
                success=False,
                action_type=ActionType.CREATE_PAYMENT_LINK,
                error_code="ADAPTER_ERROR",
                error_message=str(e),
                retryable=True,
            )

    async def resend_payment_link(
        self, case: RecoveryCase, params: dict[str, Any]
    ) -> ToolResponse:
        """Resend an existing payment link notification."""
        link_id = params.get("payment_link_id")
        if not link_id:
            return ToolResponse(
                success=False,
                action_type=ActionType.RESEND_PAYMENT_LINK,
                error_code="MISSING_PARAM",
                error_message="payment_link_id is required for resend.",
            )

        try:
            medium = params.get("medium", "sms")
            result = await self.client.resend_payment_link(link_id, medium)
            return ToolResponse(
                success=True,
                action_type=ActionType.RESEND_PAYMENT_LINK,
                external_reference=link_id,
                data={"result": result, "medium": medium},
            )
        except RazorpayAPIError as e:
            return ToolResponse(
                success=False,
                action_type=ActionType.RESEND_PAYMENT_LINK,
                error_code=e.error.code,
                error_message=e.error.description,
                retryable=e.error.status_code >= 500,
            )

    async def retry_payment(
        self, case: RecoveryCase, params: dict[str, Any]
    ) -> ToolResponse:
        """
        Retry a failed payment by creating a new payment link.
        
        Note: Razorpay doesn't support directly retrying a payment.
        A retry is implemented as creating a new payment link.
        """
        return await self.create_payment_link(case, params)

    async def schedule_retry(
        self, case: RecoveryCase, params: dict[str, Any]
    ) -> ToolResponse:
        """
        Schedule a delayed retry.
        
        For the MVP, this creates a payment link with a future expiry.
        A production system would use a job queue.
        """
        return await self.create_payment_link(case, params)
