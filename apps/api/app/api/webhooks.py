import json
from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.common import APIResponse
from app.integrations.razorpay.webhook_handler import WebhookHandler

router = APIRouter(tags=["webhooks"])

@router.post("/razorpay", response_model=APIResponse)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header("", alias="X-Razorpay-Signature"),
    db: AsyncSession = Depends(get_db)
):
    raw_body = await request.body()
    payload = {}
    if raw_body:
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception:
            payload = {}
            
    handler = WebhookHandler(db)
    event = await handler.process_event(raw_body, x_razorpay_signature, payload)
    
    return APIResponse(
        data={
            "event_id": str(event.id),
            "event_type": event.event_type,
            "status": event.processing_status.value if hasattr(event.processing_status, 'value') else str(event.processing_status),
            "signature_valid": event.signature_valid
        },
        request_id=getattr(request.state, "request_id", None)
    )
