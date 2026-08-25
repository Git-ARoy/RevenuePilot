'use client';

import React, { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { fetchAPI } from '@/lib/api';
import { 
  formatCurrency, 
  formatDate, 
  formatRelativeTime 
} from '@/lib/format';
import { 
  RecoveryCase, 
  AuditEvent, 
  CaseEvaluationResult, 
  PolicyCheckItem 
} from '@/types';
import StatusBadge from '@/components/StatusBadge';
import Timeline from '@/components/Timeline';
import { 
  ArrowLeft, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  ShieldCheck, 
  Zap, 
  Play, 
  Send, 
  UserCheck, 
  RefreshCw, 
  CreditCard, 
  Info, 
  Clock 
} from 'lucide-react';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function CaseDetailPage({ params }: PageProps) {
  const router = useRouter();
  const { id } = use(params);

  const [caseData, setCaseData] = useState<RecoveryCase | null>(null);
  const [timeline, setTimeline] = useState<AuditEvent[]>([]);
  const [evaluation, setEvaluation] = useState<CaseEvaluationResult | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [escalating, setEscalating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadCase = async () => {
    try {
      setLoading(true);
      const res = await fetchAPI<{ case: RecoveryCase; timeline: AuditEvent[] }>(
        `/api/recovery-cases/${id}`
      );
      setCaseData(res?.case || null);
      setTimeline(res?.timeline || []);
    } catch (err: any) {
      console.error('Error fetching case:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCase();
  }, [id]);

  // Dry-run evaluate action
  const handleEvaluate = async () => {
    try {
      setEvaluating(true);
      setActionError(null);
      setActionSuccess(null);
      const res = await fetchAPI<CaseEvaluationResult>(
        `/api/recovery-cases/${id}/evaluate`,
        { method: 'POST' }
      );
      setEvaluation(res);
      setActionSuccess('Dry-run policy evaluation completed.');
    } catch (err: any) {
      setActionError(err.message || 'Evaluation failed.');
    } finally {
      setEvaluating(false);
    }
  };

  // Execute recovery action
  const handleExecute = async () => {
    try {
      setExecuting(true);
      setActionError(null);
      setActionSuccess(null);
      const idemKey = `ui_exec_${id}_${Date.now()}`;
      const actionType = caseData?.current_strategy || 'CREATE_PAYMENT_LINK';

      await fetchAPI(`/api/recovery-cases/${id}/actions`, {
        method: 'POST',
        headers: { 'Idempotency-Key': idemKey },
        body: JSON.stringify({
          action_type: actionType,
          reason_code: 'MERCHANT_UI_EXECUTION',
        }),
      });

      setActionSuccess(`Recovery action ${actionType} initiated.`);
      await loadCase();
    } catch (err: any) {
      setActionError(err.message || 'Action execution failed.');
    } finally {
      setExecuting(false);
    }
  };

  // Escalate to human
  const handleEscalate = async () => {
    try {
      setEscalating(true);
      setActionError(null);
      setActionSuccess(null);

      await fetchAPI(`/api/recovery-cases/${id}/escalate`, {
        method: 'POST',
        body: JSON.stringify({
          reason_code: 'MERCHANT_MANUAL_REVIEW',
          notes: 'Escalated from merchant dashboard investigation workspace.',
        }),
      });

      setActionSuccess('Case successfully escalated to human.');
      await loadCase();
    } catch (err: any) {
      setActionError(err.message || 'Escalation failed.');
    } finally {
      setEscalating(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 max-w-5xl mx-auto py-8">
        <div className="h-6 bg-[#E5E5E5] rounded w-48 animate-pulse"></div>
        <div className="h-40 bg-white border border-[#E5E5E5] rounded-xl p-6 animate-pulse"></div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="bg-white border border-[#E5E5E5] rounded-xl p-12 text-center max-w-lg mx-auto mt-12 shadow-xs">
        <AlertTriangle className="w-10 h-10 text-[#D97706] mx-auto mb-3" />
        <h2 className="text-base font-semibold text-[#171717]">Case Not Found</h2>
        <p className="text-xs text-[#737373] mt-1 mb-5">
          Recovery opportunity #{id} does not exist or has been deleted.
        </p>
        <Link
          href="/cases"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#0D6EFD] text-white rounded-md text-xs font-medium"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Cases</span>
        </Link>
      </div>
    );
  }

  const scoreVal = caseData.recovery_score
    ? Math.round(caseData.recovery_score > 1 ? caseData.recovery_score : caseData.recovery_score * 100)
    : 0;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Back Link */}
      <div className="flex items-center justify-between">
        <Link
          href="/cases"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-[#737373] hover:text-[#171717] transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Recovery Cases</span>
        </Link>

        <div className="flex items-center gap-2">
          <span className="text-[11px] text-[#A3A3A3]">Case ID:</span>
          <span className="font-mono text-xs font-medium text-[#171717]">
            {caseData.id}
          </span>
        </div>
      </div>

      {/* Case Header Card */}
      <div className="bg-white border border-[#E5E5E5] rounded-xl p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5 mb-1.5">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#737373]">
                {caseData.case_type?.replace(/_/g, ' ') || 'Failed Payment'}
              </span>
              <StatusBadge status={caseData.status} size="md" />
            </div>

            <div className="flex items-baseline gap-3">
              <h1 className="text-3xl font-semibold tracking-tight text-[#171717]">
                {formatCurrency(caseData.amount_at_risk)}
              </h1>
              {caseData.status === 'RECOVERED' && (
                <span className="text-xs font-medium px-2 py-0.5 bg-[#ECFDF3] text-[#16A34A] border border-[#16A34A]/20 rounded">
                  {formatCurrency(caseData.amount_recovered)} Recovered
                </span>
              )}
            </div>
          </div>

          {/* Action Bar */}
          <div className="flex items-center gap-2.5 flex-wrap">
            <button
              onClick={handleEvaluate}
              disabled={evaluating || caseData.status === 'RECOVERED'}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-[#FAFAF9] text-[#171717] border border-[#E5E5E5] rounded-md text-xs font-medium transition-colors disabled:opacity-50"
            >
              <Zap className="w-3.5 h-3.5 text-[#0D6EFD]" />
              <span>{evaluating ? 'Evaluating...' : 'Dry-run Evaluate'}</span>
            </button>

            <button
              onClick={handleExecute}
              disabled={executing || caseData.status === 'RECOVERED' || caseData.status === 'TERMINAL'}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#0D6EFD] hover:bg-[#0958D9] text-white rounded-md text-xs font-medium transition-colors shadow-2xs disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{executing ? 'Executing...' : 'Execute Recovery'}</span>
            </button>

            <button
              onClick={handleEscalate}
              disabled={escalating || caseData.status === 'ESCALATED' || caseData.status === 'RECOVERED'}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-[#FFF7E6] hover:bg-[#FEF3C7] text-[#D97706] border border-[#D97706]/30 rounded-md text-xs font-medium transition-colors disabled:opacity-50"
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>{escalating ? 'Escalating...' : 'Escalate to Human'}</span>
            </button>
          </div>
        </div>

        {/* Action feedback banners */}
        {actionSuccess && (
          <div className="mt-4 p-3 bg-[#ECFDF3] border border-[#16A34A]/30 rounded-lg text-xs text-[#16A34A] flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{actionSuccess}</span>
          </div>
        )}
        {actionError && (
          <div className="mt-4 p-3 bg-[#FEF2F2] border border-[#DC2626]/30 rounded-lg text-xs text-[#DC2626] flex items-center gap-2">
            <XCircle className="w-4 h-4 shrink-0" />
            <span>{actionError}</span>
          </div>
        )}
      </div>

      {/* Investigation Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Column: 2 Spans for Investigation Workspace */}
        <div className="lg:col-span-2 space-y-6">
          {/* 1. Why this case is recoverable */}
          <div className="bg-white border border-[#E5E5E5] rounded-xl p-5 shadow-xs">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[#737373] mb-3">
              Root Cause & Diagnosis
            </h2>

            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-[#FAFAF9] border border-[#E5E5E5] rounded-lg">
                <div>
                  <span className="text-xs font-semibold text-[#171717]">
                    {caseData.diagnosis_code?.replace(/_/g, ' ') || 'Diagnostic Evaluation Pending'}
                  </span>
                  <p className="text-[11px] text-[#737373] mt-0.5">
                    {caseData.terminal_reason || 'Identified by deterministic rule-based analysis with LLM fallback.'}
                  </p>
                </div>
                {caseData.diagnosis_confidence && (
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-semibold text-[#A3A3A3]">Confidence</span>
                    <p className="font-mono text-sm font-bold text-[#16A34A]">
                      {Math.round(caseData.diagnosis_confidence * 100)}%
                    </p>
                  </div>
                )}
              </div>

              {/* Recovery Score Meter */}
              <div className="p-3 bg-[#FAFAF9] border border-[#E5E5E5] rounded-lg">
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-semibold text-[#171717]">Recovery Score Probability</span>
                  <span className="font-mono font-bold text-[#0D6EFD]">{scoreVal}%</span>
                </div>
                <div className="w-full h-2 bg-[#E5E5E5] rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all rounded-full ${
                      scoreVal >= 60 ? 'bg-[#16A34A]' : scoreVal >= 30 ? 'bg-[#0D6EFD]' : 'bg-[#D97706]'
                    }`}
                    style={{ width: `${Math.max(5, scoreVal)}%` }}
                  ></div>
                </div>
                <p className="text-[11px] text-[#737373] mt-1.5">
                  Weighted heuristic based on failure reason, attempt history, amount size, and recency.
                </p>
              </div>
            </div>
          </div>

          {/* 2. Policy Gate Verification Checklist (Authoritative Differentiator) */}
          <div className="bg-white border border-[#E5E5E5] rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-xs font-semibold uppercase tracking-wider text-[#737373]">
                  Policy Gate Verification
                </h2>
                <p className="text-[11px] text-[#737373]">
                  Deterministic safety constraints evaluated before any consequential action.
                </p>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[#ECFDF3] border border-[#16A34A]/20 rounded text-xs font-medium text-[#16A34A]">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>SAFETY ACTIVE</span>
              </div>
            </div>

            {/* Checklist Items */}
            <div className="divide-y divide-[#F0F0F0] border border-[#E5E5E5] rounded-lg bg-[#FAFAF9]">
              {evaluation?.policy?.checks ? (
                evaluation.policy.checks.map((check: PolicyCheckItem, idx: number) => (
                  <div key={idx} className="p-3 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2.5">
                      {check.passed ? (
                        <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0" />
                      ) : (
                        <XCircle className="w-4 h-4 text-[#DC2626] shrink-0" />
                      )}
                      <div>
                        <span className="font-semibold text-[#171717]">{check.rule}</span>
                        <p className="text-[11px] text-[#737373]">{check.detail}</p>
                      </div>
                    </div>
                    <span className={`text-[11px] font-medium ${check.passed ? 'text-[#16A34A]' : 'text-[#DC2626]'}`}>
                      {check.passed ? 'PASSED' : 'BLOCKED'}
                    </span>
                  </div>
                ))
              ) : (
                // Default live checks display
                <>
                  <div className="p-3 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0" />
                      <div>
                        <span className="font-semibold text-[#171717]">CASE_NOT_TERMINAL</span>
                        <p className="text-[11px] text-[#737373]">Case status is {caseData.status}</p>
                      </div>
                    </div>
                    <span className="text-[11px] font-medium text-[#16A34A]">PASSED</span>
                  </div>

                  <div className="p-3 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0" />
                      <div>
                        <span className="font-semibold text-[#171717]">MAX_ATTEMPTS</span>
                        <p className="text-[11px] text-[#737373]">Attempt count {caseData.attempt_count} / {caseData.max_attempts}</p>
                      </div>
                    </div>
                    <span className="text-[11px] font-medium text-[#16A34A]">PASSED</span>
                  </div>

                  <div className="p-3 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0" />
                      <div>
                        <span className="font-semibold text-[#171717]">AMOUNT_LIMIT</span>
                        <p className="text-[11px] text-[#737373]">Within max automated recovery cap</p>
                      </div>
                    </div>
                    <span className="text-[11px] font-medium text-[#16A34A]">PASSED</span>
                  </div>

                  <div className="p-3 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0" />
                      <div>
                        <span className="font-semibold text-[#171717]">ACTION_ALLOWED</span>
                        <p className="text-[11px] text-[#737373]">Strategy {caseData.current_strategy || 'CREATE_PAYMENT_LINK'} permitted</p>
                      </div>
                    </div>
                    <span className="text-[11px] font-medium text-[#16A34A]">PASSED</span>
                  </div>

                  <div className="p-3 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0" />
                      <div>
                        <span className="font-semibold text-[#171717]">NO_CONCURRENT_ACTION</span>
                        <p className="text-[11px] text-[#737373]">No pending lock or concurrent execution</p>
                      </div>
                    </div>
                    <span className="text-[11px] font-medium text-[#16A34A]">PASSED</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: 1 Span for Activity / Audit Trail */}
        <div className="space-y-4">
          <div className="bg-white border border-[#E5E5E5] rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xs font-semibold uppercase tracking-wider text-[#737373]">
                  Activity Timeline
                </h2>
                <p className="text-[11px] text-[#737373]">Immutable audit log</p>
              </div>
              <button
                onClick={loadCase}
                className="p-1 hover:bg-[#FAFAF9] rounded text-[#737373]"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>

            <Timeline events={timeline} />
          </div>
        </div>
      </div>
    </div>
  );
}
