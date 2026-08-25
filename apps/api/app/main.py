import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.core.database import init_db, async_sessionmaker
from app.core.config import settings

from app.api.dashboard import router as dashboard_router
from app.api.recovery_cases import router as recovery_cases_router
from app.api.policies import router as policies_router
from app.api.simulation import router as simulation_router
from app.api.webhooks import router as webhooks_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
    # Create default merchant and policy config if they don't exist
    from sqlalchemy import select
    from app.models.merchant import Merchant
    from app.models.policy_config import PolicyConfig
    from app.models.enums import ActionType
    
    async with async_sessionmaker() as session:
        try:
            result = await session.execute(select(Merchant).limit(1))
            merchant = result.scalar_one_or_none()
            if not merchant:
                merchant = Merchant(name="Default Merchant", mode="test")
                session.add(merchant)
                await session.flush()
                
                policy = PolicyConfig(
                    merchant_id=merchant.id,
                    max_attempts=3,
                    retry_cooldown_seconds=3600,
                    max_automated_recovery_amount=1000000,
                    human_approval_threshold=500000,
                    allowed_actions=[
                        ActionType.RETRY_PAYMENT.value,
                        ActionType.CREATE_PAYMENT_LINK.value,
                        ActionType.SEND_RECOVERY_PROMPT.value,
                        ActionType.ESCALATE_TO_HUMAN.value,
                        ActionType.STOP_RECOVERY.value
                    ]
                )
                session.add(policy)
                await session.commit()
        except Exception as e:
            logging.error(f"Error initializing default merchant/policy: {e}")
            await session.rollback()
            
    yield

app = FastAPI(
    title='RevenuePilot API',
    description='AI-assisted revenue recovery agent for Razorpay merchants',
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "data": None,
            "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(exc)},
            "request_id": getattr(request.state, "request_id", None)
        }
    )

app.include_router(dashboard_router, prefix="/api/dashboard")
app.include_router(recovery_cases_router, prefix="/api/recovery-cases")
app.include_router(policies_router, prefix="/api/policies")
app.include_router(simulation_router, prefix="/api/simulation")
app.include_router(webhooks_router, prefix="/api/webhooks")

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
