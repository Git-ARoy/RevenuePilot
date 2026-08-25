"""
Razorpay Webhook Handler — Signature verification and event processing.

Handles:
- Raw body preservation for signature verification
- HMAC-SHA256 signature validation
- Event deduplication
- Idempotent state processing
"""
import hmac
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import WebhookProcessingStatus, AuditEventType, ActorType
from app.models.webhook_event import WebhookEvent
from app.models.audit_event import AuditEvent


class WebhookHandler:
    """Handles Razorpay webhook events with signature verification."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

    def verify_signature(self, raw_body: bytes, signature: str) -> bool:
        """
        Verify Razorpay webhook signature.
        
        Razorpay signs webhooks with HMAC-SHA256 using the webhook secret.
        The signature is passed in the X-Razorpay-Signature header.
        """
        if not self.webhook_secret:
            # If no webhook secret configured, skip verification in dev mode
            return True

        expected = hmac.new(
            self.webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    async def process_event(
        self,
        raw_body: bytes,
        signature: str,
        payload: dict,
    ) -> WebhookEvent:
        """
        Process an incoming Razorpay webhook event.
        
        Steps:
        1. Verify signature
        2. Check for duplicate events
        3. Persist raw event
        4. Route to appropriate handler
        """
        # Step 1: Verify signature
        signature_valid = self.verify_signature(raw_body, signature)

        # Extract event metadata
        event_type = payload.get("event", "unknown")
        provider_event_id = payload.get("account_id", "") + "_" + str(
            payload.get("payload", {})
            .get("payment", {})
            .get("entity", {})
            .get("id", uuid.uuid4().hex)
        )

        # Step 2: Check for duplicate events
        existing = await self._find_existing_event(provider_event_id)
        if existing:
            existing.processing_status = WebhookProcessingStatus.DUPLICATE
            await self.db.flush()
            return existing

        # Step 3: Persist raw event
        event = WebhookEvent(
            id=uuid.uuid4(),
            provider="razorpay",
            provider_event_id=provider_event_id,
            event_type=event_type,
            signature_valid=signature_valid,
            payload=payload,
            received_at=datetime.now(timezone.utc),
            processing_status=(
                WebhookProcessingStatus.PENDING
                if signature_valid
                else WebhookProcessingStatus.FAILED
            ),
        )
        self.db.add(event)
        await self.db.flush()

        if not signature_valid:
            return event

        # Step 4: Route to handler
        try:
            await self._handle_event(event, payload)
            event.processing_status = WebhookProcessingStatus.PROCESSED
            event.processed_at = datetime.now(timezone.utc)
        except Exception as e:
            event.processing_status = WebhookProcessingStatus.FAILED
            event.processed_at = datetime.now(timezone.utc)

        await self.db.flush()
        return event

    async def _handle_event(self, event: WebhookEvent, payload: dict) -> None:
        """Route event to the appropriate handler based on event type."""
        handlers = {
            "payment.authorized": self._handle_payment_event,
            "payment.captured": self._handle_payment_event,
            "payment.failed": self._handle_payment_event,
            "order.paid": self._handle_order_event,
            "payment_link.paid": self._handle_payment_link_event,
            "payment_link.expired": self._handle_payment_link_event,
            "payment_link.cancelled": self._handle_payment_link_event,
        }

        handler = handlers.get(event.event_type)
        if handler:
            await handler(event, payload)

    async def _handle_payment_event(
        self, event: WebhookEvent, payload: dict
    ) -> None:
        """Handle payment-related webhook events."""
        payment_entity = (
            payload.get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )

        if not payment_entity:
            return

        # Create audit event for tracking
        audit = AuditEvent(
            id=uuid.uuid4(),
            event_type=AuditEventType.PAYMENT_RECONCILED,
            actor_type=ActorType.RAZORPAY_WEBHOOK,
            metadata_={
                "webhook_event_id": str(event.id),
                "event_type": event.event_type,
                "payment_id": payment_entity.get("id"),
                "payment_status": payment_entity.get("status"),
                "amount": payment_entity.get("amount"),
            },
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(audit)

    async def _handle_order_event(
        self, event: WebhookEvent, payload: dict
    ) -> None:
        """Handle order-related webhook events."""
        order_entity = (
            payload.get("payload", {})
            .get("order", {})
            .get("entity", {})
        )
        if order_entity:
            audit = AuditEvent(
                id=uuid.uuid4(),
                event_type=AuditEventType.PAYMENT_RECONCILED,
                actor_type=ActorType.RAZORPAY_WEBHOOK,
                metadata_={
                    "webhook_event_id": str(event.id),
                    "event_type": event.event_type,
                    "order_id": order_entity.get("id"),
                    "order_status": order_entity.get("status"),
                },
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(audit)

    async def _handle_payment_link_event(
        self, event: WebhookEvent, payload: dict
    ) -> None:
        """Handle payment link webhook events."""
        link_entity = (
            payload.get("payload", {})
            .get("payment_link", {})
            .get("entity", {})
        )
        if link_entity:
            audit = AuditEvent(
                id=uuid.uuid4(),
                event_type=AuditEventType.PAYMENT_RECONCILED,
                actor_type=ActorType.RAZORPAY_WEBHOOK,
                metadata_={
                    "webhook_event_id": str(event.id),
                    "event_type": event.event_type,
                    "payment_link_id": link_entity.get("id"),
                    "link_status": link_entity.get("status"),
                },
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(audit)

    async def _find_existing_event(
        self, provider_event_id: str
    ) -> Optional[WebhookEvent]:
        """Check for duplicate events."""
        result = await self.db.execute(
            select(WebhookEvent).where(
                WebhookEvent.provider_event_id == provider_event_id
            )
        )
        return result.scalar_one_or_none()
