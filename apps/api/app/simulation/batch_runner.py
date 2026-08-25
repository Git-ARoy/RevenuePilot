"""
Batch Runner — Processes all cases in a simulation batch through the full agent loop.

Coordinates:
1. Take a generated batch of cases
2. Run each case through the recovery orchestrator
3. Simulate outcomes (payment events) for acted-upon cases
4. Compute and store batch-level metrics
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    CaseStatus, BatchStatus, ActionType, AttemptStatus,
    AuditEventType, ActorType,
)
from app.models.recovery_case import RecoveryCase
from app.models.recovery_attempt import RecoveryAttempt
from app.models.batch_run import BatchRun
from app.models.payment import Payment
from app.models.audit_event import AuditEvent
from app.integrations.simulation.adapter import SimulationAdapter
from app.simulation.outcome_simulator import OutcomeSimulator


class BatchRunner:
    """Runs a simulation batch through the full recovery pipeline."""

    def __init__(self, db: AsyncSession, seed: int = 42):
        self.db = db
        self.seed = seed

    async def run_batch(self, batch_id: uuid.UUID) -> dict:
        """
        Process all cases in a batch through the full agent loop.
        
        Returns computed batch metrics.
        """
        # Get batch
        result = await self.db.execute(
            select(BatchRun).where(BatchRun.id == batch_id)
        )
        batch = result.scalar_one_or_none()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        # Update batch status
        batch.status = BatchStatus.RUNNING
        batch.started_at = datetime.now(timezone.utc)
        await self.db.flush()

        try:
            # Get all cases in this batch that need processing
            cases_result = await self.db.execute(
                select(RecoveryCase).where(
                    and_(
                        RecoveryCase.batch_id == batch_id,
                        RecoveryCase.status.notin_([
                            CaseStatus.RECOVERED.value,
                            CaseStatus.TERMINAL.value,
                            CaseStatus.STOPPED.value,
                        ]),
                    )
                )
            )
            cases = list(cases_result.scalars().all())

            # Import orchestrator here to avoid circular imports
            from app.services.orchestrator import RecoveryOrchestrator

            # Create simulation adapter
            sim_adapter = SimulationAdapter(seed=self.seed, inject_failures=True)

            # Create orchestrator with simulation adapter
            orchestrator = RecoveryOrchestrator(
                db=self.db,
                adapter=sim_adapter,
            )

            # Process each case
            for case in cases:
                try:
                    await orchestrator.process_case(case.id)
                except Exception as e:
                    # Individual case failures shouldn't stop the batch
                    case.status = CaseStatus.TERMINAL
                    case.terminal_reason = f"Batch processing error: {str(e)[:200]}"

            # Simulate outcomes for cases waiting for payment
            outcome_sim = OutcomeSimulator(db=self.db, seed=self.seed)
            await outcome_sim.resolve_pending_outcomes(batch_id)

            # Compute metrics
            metrics = await self._compute_metrics(batch_id)

            # Update batch
            batch.status = BatchStatus.COMPLETED
            batch.completed_at = datetime.now(timezone.utc)
            batch.amount_recovered = metrics.get("amount_recovered", 0)
            batch.recovery_rate = metrics.get("recovery_rate", 0.0)
            batch.metrics = metrics

            await self.db.commit()
            return metrics

        except Exception as e:
            batch.status = BatchStatus.FAILED
            batch.completed_at = datetime.now(timezone.utc)
            batch.metrics = {"error": str(e)}
            await self.db.commit()
            raise

    async def _compute_metrics(self, batch_id: uuid.UUID) -> dict:
        """Compute comprehensive batch-level metrics."""
        # Total cases
        total_result = await self.db.execute(
            select(func.count()).where(RecoveryCase.batch_id == batch_id)
        )
        total_cases = total_result.scalar() or 0

        # Amount at risk
        risk_result = await self.db.execute(
            select(func.sum(RecoveryCase.amount_at_risk)).where(
                RecoveryCase.batch_id == batch_id
            )
        )
        amount_at_risk = int(risk_result.scalar() or 0)

        # Recovered cases
        recovered_result = await self.db.execute(
            select(func.count()).where(
                and_(
                    RecoveryCase.batch_id == batch_id,
                    RecoveryCase.status == CaseStatus.RECOVERED,
                )
            )
        )
        recovered_cases = int(recovered_result.scalar() or 0)

        # Amount recovered
        amount_recovered_result = await self.db.execute(
            select(func.sum(RecoveryCase.amount_recovered)).where(
                and_(
                    RecoveryCase.batch_id == batch_id,
                    RecoveryCase.status == CaseStatus.RECOVERED,
                )
            )
        )
        amount_recovered = int(amount_recovered_result.scalar() or 0)

        # Escalated cases
        escalated_result = await self.db.execute(
            select(func.count()).where(
                and_(
                    RecoveryCase.batch_id == batch_id,
                    RecoveryCase.status == CaseStatus.ESCALATED,
                )
            )
        )
        escalations = int(escalated_result.scalar() or 0)

        # Failed/terminal cases
        failed_result = await self.db.execute(
            select(func.count()).where(
                and_(
                    RecoveryCase.batch_id == batch_id,
                    RecoveryCase.status.in_([
                        CaseStatus.TERMINAL.value,
                        CaseStatus.ACTION_FAILED.value,
                    ]),
                )
            )
        )
        terminal_failures = int(failed_result.scalar() or 0)

        # Actions attempted
        actions_result = await self.db.execute(
            select(func.count()).select_from(RecoveryAttempt).join(
                RecoveryCase,
                RecoveryAttempt.recovery_case_id == RecoveryCase.id,
            ).where(RecoveryCase.batch_id == batch_id)
        )
        actions_attempted = int(actions_result.scalar() or 0)

        # Eligible cases (non-already-recovered, non-terminal at start)
        eligible_result = await self.db.execute(
            select(func.count()).where(
                and_(
                    RecoveryCase.batch_id == batch_id,
                    RecoveryCase.amount_at_risk > 0,
                )
            )
        )
        eligible_cases = int(eligible_result.scalar() or 0)

        # Recovery rate
        recovery_rate = float(
            (amount_recovered / amount_at_risk * 100) if amount_at_risk > 0 else 0.0
        )

        # Stopped cases
        stopped_result = await self.db.execute(
            select(func.count()).where(
                and_(
                    RecoveryCase.batch_id == batch_id,
                    RecoveryCase.status == CaseStatus.STOPPED,
                )
            )
        )
        stopped = int(stopped_result.scalar() or 0)

        return {
            "cases": total_cases,
            "eligible_cases": eligible_cases,
            "amount_at_risk": amount_at_risk,
            "amount_recovered": amount_recovered,
            "recovery_rate": round(recovery_rate, 2),
            "recovered_cases": recovered_cases,
            "actions_attempted": actions_attempted,
            "escalations": escalations,
            "terminal_failures": terminal_failures,
            "stopped": stopped,
        }
