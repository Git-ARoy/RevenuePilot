import os

base_dir = "/Users/aroy/Documents/RevenuePilot/apps/api"

files_content = {
    "app/__init__.py": "",
    "app/core/__init__.py": "",
    "app/core/config.py": """from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/db"
    DATABASE_URL_SYNC: str = "postgresql://user:pass@localhost/db"
    
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    RAZORPAY_MODE: str = "test"
    
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "secret"
    
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings()
""",
    "app/core/database.py": """from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_db():
    async with async_sessionmaker() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        pass
""",
    "app/models/__init__.py": """from app.core.database import Base
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.order import Order
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.recovery_attempt import RecoveryAttempt
from app.models.agent_decision import AgentDecision
from app.models.webhook_event import WebhookEvent
from app.models.audit_event import AuditEvent
from app.models.batch_run import BatchRun
from app.models.policy_config import PolicyConfig
""",
    "app/models/enums.py": """import enum

class CaseStatus(str, enum.Enum):
    DETECTED = "DETECTED"
    DIAGNOSED = "DIAGNOSED"
    ELIGIBILITY_CHECKED = "ELIGIBILITY_CHECKED"
    BLOCKED = "BLOCKED"
    STRATEGY_SELECTED = "STRATEGY_SELECTED"
    ACTION_PENDING = "ACTION_PENDING"
    ACTION_EXECUTING = "ACTION_EXECUTING"
    ACTION_FAILED = "ACTION_FAILED"
    RETRY_PENDING = "RETRY_PENDING"
    WAITING_FOR_OUTCOME = "WAITING_FOR_OUTCOME"
    RECOVERED = "RECOVERED"
    UNRECOVERED = "UNRECOVERED"
    ESCALATED = "ESCALATED"
    STOPPED = "STOPPED"
    TERMINAL = "TERMINAL"

class CaseType(str, enum.Enum):
    FAILED_PAYMENT = "FAILED_PAYMENT"
    REPEATED_FAILURE = "REPEATED_FAILURE"
    ABANDONED_CHECKOUT = "ABANDONED_CHECKOUT"
    FAILED_RECURRING = "FAILED_RECURRING"
    EXPIRED_OPPORTUNITY = "EXPIRED_OPPORTUNITY"

class DiagnosisCode(str, enum.Enum):
    TRANSIENT_GATEWAY_FAILURE = "TRANSIENT_GATEWAY_FAILURE"
    CUSTOMER_ACTION_REQUIRED = "CUSTOMER_ACTION_REQUIRED"
    PAYMENT_METHOD_FAILURE = "PAYMENT_METHOD_FAILURE"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    EXPIRED_PAYMENT_METHOD = "EXPIRED_PAYMENT_METHOD"
    BANK_DECLINE = "BANK_DECLINE"
    UNKNOWN_PAYMENT_FAILURE = "UNKNOWN_PAYMENT_FAILURE"
    NON_RECOVERABLE = "NON_RECOVERABLE"
    ALREADY_RECOVERED = "ALREADY_RECOVERED"

class ActionType(str, enum.Enum):
    RETRY_PAYMENT = "RETRY_PAYMENT"
    CREATE_PAYMENT_LINK = "CREATE_PAYMENT_LINK"
    RESEND_PAYMENT_LINK = "RESEND_PAYMENT_LINK"
    SCHEDULE_RETRY = "SCHEDULE_RETRY"
    SEND_RECOVERY_PROMPT = "SEND_RECOVERY_PROMPT"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"
    STOP_RECOVERY = "STOP_RECOVERY"

class AttemptStatus(str, enum.Enum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class ActorType(str, enum.Enum):
    SYSTEM = "SYSTEM"
    AGENT = "AGENT"
    MERCHANT = "MERCHANT"
    RAZORPAY_WEBHOOK = "RAZORPAY_WEBHOOK"

class AuditEventType(str, enum.Enum):
    CASE_DETECTED = "CASE_DETECTED"
    CASE_DIAGNOSED = "CASE_DIAGNOSED"
    ACTION_PROPOSED = "ACTION_PROPOSED"
    ACTION_BLOCKED = "ACTION_BLOCKED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    ACTION_FAILED = "ACTION_FAILED"
    PAYMENT_RECONCILED = "PAYMENT_RECONCILED"
    RECOVERY_VERIFIED = "RECOVERY_VERIFIED"
    CASE_ESCALATED = "CASE_ESCALATED"
    CASE_STOPPED = "CASE_STOPPED"
    POLICY_UPDATED = "POLICY_UPDATED"

class WebhookProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    DUPLICATE = "DUPLICATE"

class BatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
""",
    "app/models/merchant.py": """import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    razorpay_key_id = Column(String, nullable=True)
    mode = Column(String, default='test')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
""",
    "app/models/customer.py": """import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey('merchants.id'), nullable=False)
    external_customer_id = Column(String, nullable=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    metadata_ = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
""",
    "app/models/order.py": """import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey('merchants.id'), nullable=False)
    razorpay_order_id = Column(String, unique=True, nullable=True)
    amount = Column(BigInteger, nullable=False)
    currency = Column(String(3), default='INR')
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
""",
    "app/models/payment.py": """import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, BigInteger, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey('merchants.id'), nullable=False)
    razorpay_payment_id = Column(String, unique=True, nullable=True)
    razorpay_order_id = Column(String, nullable=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=True)
    amount = Column(BigInteger, nullable=False)
    currency = Column(String(3), default='INR')
    status = Column(String, nullable=False)
    method = Column(String, nullable=True)
    error_code = Column(String, nullable=True)
    error_description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
""",
    "app/models/recovery_case.py": """import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, BigInteger, Enum as SQLEnum, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import CaseType, CaseStatus, DiagnosisCode, ActionType

class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey('merchants.id'), nullable=False)
    payment_id = Column(UUID(as_uuid=True), ForeignKey('payments.id'), nullable=False)
    batch_id = Column(UUID(as_uuid=True), nullable=True) # Assuming batch_runs table might be created later or ForeignKey omitted if ok
    case_type = Column(SQLEnum(CaseType), nullable=False)
    amount_at_risk = Column(BigInteger, nullable=False)
    amount_recovered = Column(BigInteger, default=0)
    currency = Column(String(3), default='INR')
    status = Column(SQLEnum(CaseStatus), default=CaseStatus.DETECTED)
    diagnosis_code = Column(SQLEnum(DiagnosisCode), nullable=True)
    diagnosis_confidence = Column(Float, nullable=True)
    recovery_score = Column(Float, nullable=True)
    current_strategy = Column(SQLEnum(ActionType), nullable=True)
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    next_eligible_at = Column(DateTime(timezone=True), nullable=True)
    terminal_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
""",
    "app/models/recovery_attempt.py": """import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum as SQLEnum, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.enums import ActionType, AttemptStatus

class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recovery_case_id = Column(UUID(as_uuid=True), ForeignKey('recovery_cases.id'), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    action_type = Column(SQLEnum(ActionType), nullable=False)
    status = Column(SQLEnum(AttemptStatus), nullable=False)
    idempotency_key = Column(String, unique=True, nullable=False)
    tool_request_hash = Column(String, nullable=True)
    tool_response = Column(JSON, nullable=True)
    external_reference = Column(String, nullable=True)
    error_code = Column(String, nullable=True)
    error_description = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
""",
    "app/models/agent_decision.py": """import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class AgentDecision(Base):
    __tablename__ = "agent_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recovery_case_id = Column(UUID(as_uuid=True), ForeignKey('recovery_cases.id'), nullable=False)
    stage = Column(String, nullable=False)
    decision = Column(String, nullable=False)
    reason_code = Column(String, nullable=True)
    evidence = Column(JSON, nullable=True)
    model_provider = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
""",
    "app/models/webhook_event.py": """import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.enums import WebhookProcessingStatus

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey('merchants.id'), nullable=True)
    provider = Column(String, default='razorpay')
    provider_event_id = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    signature_valid = Column(Boolean, nullable=False)
    payload = Column(JSON, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_status = Column(SQLEnum(WebhookProcessingStatus), nullable=False)
""",
    "app/models/audit_event.py": """import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import AuditEventType, ActorType

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recovery_case_id = Column(UUID(as_uuid=True), ForeignKey('recovery_cases.id'), nullable=True)
    event_type = Column(SQLEnum(AuditEventType), nullable=False)
    actor_type = Column(SQLEnum(ActorType), nullable=False)
    actor_id = Column(String, nullable=True)
    metadata_ = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
""",
    "app/models/batch_run.py": """import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON, Enum as SQLEnum, Float, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import BatchStatus

class BatchRun(Base):
    __tablename__ = "batch_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey('merchants.id'), nullable=False)
    mode = Column(String, nullable=False)
    seed = Column(Integer, nullable=True)
    config = Column(JSON, nullable=True)
    status = Column(SQLEnum(BatchStatus), default=BatchStatus.PENDING)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    case_count = Column(Integer, default=0)
    amount_at_risk = Column(BigInteger, default=0)
    amount_recovered = Column(BigInteger, default=0)
    recovery_rate = Column(Float, default=0.0)
    metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
""",
    "app/models/policy_config.py": """import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON, Boolean, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class PolicyConfig(Base):
    __tablename__ = "policy_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey('merchants.id'), unique=True, nullable=False)
    max_attempts = Column(Integer, default=3)
    retry_cooldown_seconds = Column(Integer, default=3600)
    max_automated_recovery_amount = Column(BigInteger, default=1000000)
    human_approval_threshold = Column(BigInteger, default=500000)
    allowed_actions = Column(JSON, nullable=False)
    escalation_threshold = Column(BigInteger, default=500000)
    model_selection = Column(String, default='default')
    simulation_mode = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
""",
    "app/main.py": """import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.core.config import settings

from app.api.dashboard import router as dashboard_router
from app.api.recovery_cases import router as recovery_cases_router
from app.api.policies import router as policies_router
from app.api.simulation import router as simulation_router
from app.api.webhooks import router as webhooks_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title='RevenuePilot API',
    description='AI-assisted revenue recovery agent for Razorpay merchants',
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
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
""",
    "app/api/__init__.py": "",
    "app/api/dashboard.py": """from fastapi import APIRouter

router = APIRouter(tags=["dashboard"])

@router.get("/summary")
async def get_summary():
    return {"data": "mock_data", "error": None, "request_id": "mock_id"}
""",
    "app/api/recovery_cases.py": """from fastapi import APIRouter

router = APIRouter(tags=["recovery_cases"])

@router.get("/")
async def list_cases():
    return {"data": [], "error": None, "request_id": "mock_id"}

@router.get("/{case_id}")
async def get_case(case_id: str):
    return {"data": {"id": case_id}, "error": None, "request_id": "mock_id"}
""",
    "app/api/policies.py": """from fastapi import APIRouter

router = APIRouter(tags=["policies"])

@router.get("/")
async def get_policies():
    return {"data": [], "error": None, "request_id": "mock_id"}

@router.put("/")
async def update_policy():
    return {"data": "updated", "error": None, "request_id": "mock_id"}
""",
    "app/api/simulation.py": """from fastapi import APIRouter

router = APIRouter(tags=["simulation"])

@router.post("/generate")
async def generate():
    return {"data": "generated", "error": None, "request_id": "mock_id"}

@router.post("/batches/{batch_id}/run")
async def run_batch(batch_id: str):
    return {"data": "running", "error": None, "request_id": "mock_id"}

@router.get("/batches/{batch_id}")
async def get_batch(batch_id: str):
    return {"data": {"id": batch_id}, "error": None, "request_id": "mock_id"}
""",
    "app/api/webhooks.py": """from fastapi import APIRouter

router = APIRouter(tags=["webhooks"])

@router.post("/razorpay")
async def razorpay_webhook():
    return {"status": "ok"}
""",
    "app/schemas/__init__.py": "",
    "app/schemas/common.py": """from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar('T')

class ErrorDetail(BaseModel):
    code: str
    message: str

class APIResponse(BaseModel, Generic[T]):
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    request_id: str

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    page: int
    page_size: int
    total: int
""",
    "app/schemas/dashboard.py": """from pydantic import BaseModel

class DashboardSummaryResponse(BaseModel):
    total_cases: int
    total_recovered: int
""",
    "app/schemas/recovery_case.py": """from pydantic import BaseModel

class RecoveryCaseListResponse(BaseModel):
    pass
""",
    "app/schemas/simulation.py": """from pydantic import BaseModel

class SimulationGenerateRequest(BaseModel):
    pass
""",
    "app/schemas/policy.py": """from pydantic import BaseModel

class PolicyGet(BaseModel):
    pass
""",
    "app/services/__init__.py": "",
    "app/agents/__init__.py": "",
    "app/policies/__init__.py": "",
    "app/integrations/__init__.py": "",
    "app/integrations/razorpay/__init__.py": "",
    "app/simulation/__init__.py": "",
    "app/workers/__init__.py": "",
    "alembic.ini": """[alembic]
script_location = alembic
sqlalchemy.url = %(DATABASE_URL_SYNC)s

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""",
    "alembic/env.py": """import os
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from dotenv import load_dotenv

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

from app.core.database import Base
from app.models import *

target_metadata = Base.metadata

def get_url():
    return os.environ.get("DATABASE_URL_SYNC", "postgresql://user:pass@localhost/db")

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
""",
    "alembic/versions/__init__.py": ""
}

for rel_path, content in files_content.items():
    full_path = os.path.join(base_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print("Files created successfully.")
