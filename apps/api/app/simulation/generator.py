"""
Scenario Generator — Creates deterministic synthetic recovery cases.

Generates realistic payment failure scenarios with configurable
distribution. Uses seeded randomness for reproducibility.
"""
import uuid
import random as _random
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import CaseType, CaseStatus, DiagnosisCode, BatchStatus
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.order import Order
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.batch_run import BatchRun


# Default scenario distribution
DEFAULT_SCENARIO_MIX = {
    "transient_failure": 0.25,
    "insufficient_funds": 0.20,
    "payment_method_failure": 0.15,
    "bank_decline": 0.10,
    "checkout_abandonment": 0.10,
    "already_recovered": 0.10,
    "non_recoverable": 0.05,
    "ambiguous": 0.05,
}

# Scenario to diagnosis code mapping
SCENARIO_DIAGNOSIS_MAP = {
    "transient_failure": DiagnosisCode.TRANSIENT_GATEWAY_FAILURE,
    "insufficient_funds": DiagnosisCode.INSUFFICIENT_FUNDS,
    "payment_method_failure": DiagnosisCode.PAYMENT_METHOD_FAILURE,
    "bank_decline": DiagnosisCode.BANK_DECLINE,
    "checkout_abandonment": DiagnosisCode.CUSTOMER_ACTION_REQUIRED,
    "already_recovered": DiagnosisCode.ALREADY_RECOVERED,
    "non_recoverable": DiagnosisCode.NON_RECOVERABLE,
    "ambiguous": DiagnosisCode.UNKNOWN_PAYMENT_FAILURE,
}

# Scenario to case type mapping
SCENARIO_CASE_TYPE_MAP = {
    "transient_failure": CaseType.FAILED_PAYMENT,
    "insufficient_funds": CaseType.FAILED_PAYMENT,
    "payment_method_failure": CaseType.FAILED_PAYMENT,
    "bank_decline": CaseType.FAILED_PAYMENT,
    "checkout_abandonment": CaseType.ABANDONED_CHECKOUT,
    "already_recovered": CaseType.FAILED_PAYMENT,
    "non_recoverable": CaseType.FAILED_PAYMENT,
    "ambiguous": CaseType.FAILED_PAYMENT,
}

# Realistic error descriptions by scenario
SCENARIO_ERROR_DESCRIPTIONS = {
    "transient_failure": [
        "Payment processing failed due to gateway timeout. Please retry.",
        "Connection to payment gateway timed out. Transaction not completed.",
        "Temporary server error during payment processing.",
        "Gateway returned an unexpected error. Please try again.",
    ],
    "insufficient_funds": [
        "Your payment could not be completed due to insufficient funds.",
        "Transaction declined: insufficient balance in account.",
        "Payment failed - not enough balance to complete this transaction.",
    ],
    "payment_method_failure": [
        "Invalid card number entered. Please check and retry.",
        "Incorrect CVV provided for the card.",
        "The payment method details could not be verified.",
        "Card authentication failed. Please check card details.",
    ],
    "bank_decline": [
        "Payment declined by issuing bank. Contact your bank for details.",
        "Transaction not permitted by the card issuer.",
        "Bank declined the transaction. Do not honour.",
        "Your bank has declined this transaction.",
    ],
    "checkout_abandonment": [
        "Customer did not complete the payment process.",
        "Payment session expired before completion.",
        "Checkout abandoned - no payment attempt made.",
    ],
    "already_recovered": [
        "Payment was already captured successfully.",
        "Duplicate payment detected - original payment succeeded.",
    ],
    "non_recoverable": [
        "Payment blocked by risk assessment. Transaction flagged as suspicious.",
        "Account restricted due to compliance checks.",
        "Payment permanently declined - card reported lost or stolen.",
    ],
    "ambiguous": [
        "Payment could not be processed at this time.",
        "An error occurred during payment. Please try again later.",
        "Transaction failed due to an unspecified error.",
    ],
}

# Razorpay error codes by scenario
SCENARIO_ERROR_CODES = {
    "transient_failure": ["GATEWAY_ERROR", "SERVER_ERROR", "BAD_REQUEST_ERROR"],
    "insufficient_funds": ["BAD_REQUEST_ERROR"],
    "payment_method_failure": ["BAD_REQUEST_ERROR"],
    "bank_decline": ["BAD_REQUEST_ERROR"],
    "checkout_abandonment": ["BAD_REQUEST_ERROR"],
    "already_recovered": ["BAD_REQUEST_ERROR"],
    "non_recoverable": ["BAD_REQUEST_ERROR"],
    "ambiguous": ["BAD_REQUEST_ERROR", "SERVER_ERROR"],
}

# Sample customer data
SAMPLE_NAMES = [
    "Aarav Sharma", "Priya Patel", "Rohan Gupta", "Ananya Singh",
    "Vikram Reddy", "Neha Verma", "Arjun Kumar", "Kavya Nair",
    "Rahul Joshi", "Meera Iyer", "Aditya Rao", "Sanya Banerjee",
    "Karan Malhotra", "Divya Saxena", "Siddharth Menon",
]

PAYMENT_METHODS = ["card", "upi", "netbanking", "wallet"]


class ScenarioGenerator:
    """Generates deterministic synthetic recovery cases for batch evaluation."""

    def __init__(self, db: AsyncSession, seed: int = 42):
        self.db = db
        self.rng = _random.Random(seed)
        self.seed = seed

    async def generate_batch(
        self,
        merchant_id: uuid.UUID,
        count: int = 100,
        amount_min: int = 10000,    # ₹100 in paise
        amount_max: int = 500000,   # ₹5,000 in paise
        scenario_mix: Optional[dict[str, float]] = None,
    ) -> BatchRun:
        """
        Generate a batch of synthetic recovery cases.
        
        Returns a BatchRun record with all generated cases linked.
        """
        mix = scenario_mix or DEFAULT_SCENARIO_MIX

        # Create batch run
        batch = BatchRun(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            mode="simulation",
            seed=self.seed,
            config={
                "count": count,
                "amount_min": amount_min,
                "amount_max": amount_max,
                "scenario_mix": mix,
            },
            status=BatchStatus.PENDING,
            case_count=count,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(batch)

        # Generate scenarios based on distribution
        scenarios = self._generate_scenario_list(count, mix)

        total_at_risk = 0

        for i, scenario in enumerate(scenarios):
            # Generate customer
            customer = self._generate_customer(merchant_id, i)
            self.db.add(customer)

            # Generate order
            amount = self.rng.randint(amount_min, amount_max)
            order = self._generate_order(merchant_id, amount, i)
            self.db.add(order)

            # Generate payment
            payment = self._generate_payment(
                merchant_id, order, customer, amount, scenario, i
            )
            self.db.add(payment)

            # Generate recovery case
            case = self._generate_case(
                merchant_id, payment, batch.id, amount, scenario
            )
            self.db.add(case)

            total_at_risk += amount

        # Update batch totals
        batch.amount_at_risk = total_at_risk

        await self.db.flush()
        return batch

    def _generate_scenario_list(
        self, count: int, mix: dict[str, float]
    ) -> list[str]:
        """Generate a list of scenarios based on distribution."""
        scenarios = []
        for scenario, ratio in mix.items():
            n = max(1, round(count * ratio))
            scenarios.extend([scenario] * n)

        # Adjust to exact count
        while len(scenarios) < count:
            scenarios.append(self.rng.choice(list(mix.keys())))
        while len(scenarios) > count:
            scenarios.pop()

        self.rng.shuffle(scenarios)
        return scenarios

    def _generate_customer(
        self, merchant_id: uuid.UUID, index: int
    ) -> Customer:
        """Generate a synthetic customer."""
        name = self.rng.choice(SAMPLE_NAMES)
        first = name.split()[0].lower()
        return Customer(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            external_customer_id=f"cust_sim_{index:04d}",
            name=name,
            email=f"{first}.{index}@example.com",
            phone=f"+91{self.rng.randint(7000000000, 9999999999)}",
            created_at=datetime.now(timezone.utc),
        )

    def _generate_order(
        self, merchant_id: uuid.UUID, amount: int, index: int
    ) -> Order:
        """Generate a synthetic order."""
        return Order(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            razorpay_order_id=f"order_sim_{index:04d}_{uuid.uuid4().hex[:8]}",
            amount=amount,
            currency="INR",
            status="created",
            created_at=datetime.now(timezone.utc) - timedelta(
                minutes=self.rng.randint(30, 1440)
            ),
        )

    def _generate_payment(
        self,
        merchant_id: uuid.UUID,
        order: Order,
        customer: Customer,
        amount: int,
        scenario: str,
        index: int,
    ) -> Payment:
        """Generate a synthetic failed payment."""
        error_descriptions = SCENARIO_ERROR_DESCRIPTIONS.get(scenario, ["Unknown error"])
        error_codes = SCENARIO_ERROR_CODES.get(scenario, ["BAD_REQUEST_ERROR"])

        # Already recovered payments have status 'captured'
        status = "captured" if scenario == "already_recovered" else "failed"

        return Payment(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            razorpay_payment_id=f"pay_sim_{index:04d}_{uuid.uuid4().hex[:8]}",
            razorpay_order_id=order.razorpay_order_id,
            order_id=order.id,
            customer_id=customer.id,
            amount=amount,
            currency="INR",
            status=status,
            method=self.rng.choice(PAYMENT_METHODS),
            error_code=self.rng.choice(error_codes) if status == "failed" else None,
            error_description=(
                self.rng.choice(error_descriptions) if status == "failed" else None
            ),
            created_at=order.created_at + timedelta(
                minutes=self.rng.randint(1, 30)
            ),
        )

    def _generate_case(
        self,
        merchant_id: uuid.UUID,
        payment: Payment,
        batch_id: uuid.UUID,
        amount: int,
        scenario: str,
    ) -> RecoveryCase:
        """Generate a recovery case from a synthetic payment."""
        case_type = SCENARIO_CASE_TYPE_MAP.get(
            scenario, CaseType.FAILED_PAYMENT
        )

        # Already recovered payments start in RECOVERED status
        if scenario == "already_recovered":
            status = CaseStatus.RECOVERED
        else:
            status = CaseStatus.DETECTED

        return RecoveryCase(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            payment_id=payment.id,
            batch_id=batch_id,
            case_type=case_type,
            amount_at_risk=amount,
            amount_recovered=amount if scenario == "already_recovered" else 0,
            currency="INR",
            status=status,
            attempt_count=0,
            max_attempts=3,
            created_at=payment.created_at + timedelta(seconds=30),
        )
