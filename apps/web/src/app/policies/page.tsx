'use client';

import React, { useEffect, useState } from 'react';
import { fetchAPI } from '@/lib/api';
import { PolicyConfig } from '@/types';
import { 
  ShieldCheck, 
  Save, 
  CheckCircle2, 
  AlertCircle, 
  Activity, 
  Zap, 
  Lock, 
  HelpCircle, 
  RefreshCw 
} from 'lucide-react';

const ALL_ACTIONS = [
  { id: 'CREATE_PAYMENT_LINK', name: 'Create Payment Link', desc: 'Generates a secure Razorpay payment link sent via SMS/Email' },
  { id: 'RETRY_PAYMENT', name: 'Instant Retry', desc: 'Re-attempts transient gateway failure via fresh payment attempt' },
  { id: 'RESEND_PAYMENT_LINK', name: 'Resend Payment Link', desc: 'Resends existing payment link notification to customer' },
  { id: 'SCHEDULE_RETRY', name: 'Schedule Retry', desc: 'Queues a delayed retry attempt after the cooldown period' },
  { id: 'SEND_RECOVERY_PROMPT', name: 'Send Recovery Prompt', desc: 'Sends personalized SMS/WhatsApp recovery reminder' },
  { id: 'ESCALATE_TO_HUMAN', name: 'Escalate to Human', desc: 'Routes complex or high-value cases to merchant operations' },
  { id: 'STOP_RECOVERY', name: 'Stop Recovery', desc: 'Terminates recovery attempts for non-recoverable transactions' },
];

export default function PoliciesPage() {
  const [policy, setPolicy] = useState<PolicyConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form inputs
  const [maxAttempts, setMaxAttempts] = useState<number>(3);
  const [cooldownMinutes, setCooldownMinutes] = useState<number>(60);
  const [maxAmountRupees, setMaxAmountRupees] = useState<number>(10000);
  const [humanThresholdRupees, setHumanThresholdRupees] = useState<number>(5000);
  const [allowedActions, setAllowedActions] = useState<string[]>([]);

  const loadPolicy = async () => {
    try {
      setLoading(true);
      const res = await fetchAPI<PolicyConfig>('/api/policies');
      if (res) {
        setPolicy(res);
        setMaxAttempts(res.max_attempts);
        setCooldownMinutes(Math.round(res.retry_cooldown_seconds / 60));
        setMaxAmountRupees(Math.round(res.max_automated_recovery_amount / 100));
        setHumanThresholdRupees(Math.round(res.human_approval_threshold / 100));
        setAllowedActions(res.allowed_actions || []);
      }
    } catch (err: any) {
      console.error('Error loading policy:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicy();
  }, []);

  const handleActionToggle = (actionId: string) => {
    setAllowedActions((prev) =>
      prev.includes(actionId) ? prev.filter((a) => a !== actionId) : [...prev, actionId]
    );
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setErrorMsg(null);
      setSuccessMsg(null);

      const payload = {
        max_attempts: maxAttempts,
        retry_cooldown_seconds: cooldownMinutes * 60,
        max_automated_recovery_amount: maxAmountRupees * 100,
        human_approval_threshold: humanThresholdRupees * 100,
        allowed_actions: allowedActions,
      };

      const res = await fetchAPI<PolicyConfig>('/api/policies', {
        method: 'PUT',
        body: JSON.stringify(payload),
      });

      setPolicy(res);
      setSuccessMsg('Safety policies updated successfully. Audit event recorded.');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update policy.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#E5E5E5]">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-[#171717]">
            Safety Policies & Governance
          </h1>
          <p className="text-xs text-[#737373] mt-0.5">
            Deterministic safety gates governing automated payment recovery actions.
          </p>
        </div>

        <button
          onClick={loadPolicy}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-[#FAFAF9] text-[#171717] border border-[#E5E5E5] rounded-md text-xs font-medium transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5 text-[#737373]" />
          <span>Reload</span>
        </button>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="p-3 bg-[#ECFDF3] border border-[#16A34A]/30 rounded-lg text-xs text-[#16A34A] flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="p-3 bg-[#FEF2F2] border border-[#DC2626]/30 rounded-lg text-xs text-[#DC2626] flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Grid: Settings Form & Integration Badges */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left 2 Spans: Policy Controls Form */}
        <div className="lg:col-span-2 bg-white border border-[#E5E5E5] rounded-xl p-6 shadow-xs space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#F0F0F0]">
            <div>
              <h2 className="text-xs font-semibold uppercase tracking-wider text-[#737373]">
                Automated Recovery Bounds
              </h2>
              <p className="text-[11px] text-[#737373]">
                Strict limits enforced by the PolicyEngine before executing any tool call.
              </p>
            </div>
            <ShieldCheck className="w-4 h-4 text-[#16A34A]" />
          </div>

          <form onSubmit={handleSave} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-semibold text-[#171717] mb-1">
                  Maximum Automated Attempts
                </label>
                <input
                  type="number"
                  min={1}
                  max={5}
                  value={maxAttempts}
                  onChange={(e) => setMaxAttempts(Number(e.target.value))}
                  className="w-full px-3 py-1.5 bg-[#FAFAF9] border border-[#E5E5E5] rounded-md text-xs text-[#171717] focus:outline-none focus:border-[#0D6EFD]"
                />
                <span className="text-[10px] text-[#737373] mt-0.5 block">
                  Capped to prevent customer fatigue.
                </span>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[#171717] mb-1">
                  Retry Cooldown Period (Minutes)
                </label>
                <input
                  type="number"
                  min={5}
                  max={1440}
                  value={cooldownMinutes}
                  onChange={(e) => setCooldownMinutes(Number(e.target.value))}
                  className="w-full px-3 py-1.5 bg-[#FAFAF9] border border-[#E5E5E5] rounded-md text-xs text-[#171717] focus:outline-none focus:border-[#0D6EFD]"
                />
                <span className="text-[10px] text-[#737373] mt-0.5 block">
                  Delay before retrying transient failures.
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-[11px] font-semibold text-[#171717] mb-1">
                  Max Automated Recovery Amount (₹)
                </label>
                <input
                  type="number"
                  min={100}
                  step={500}
                  value={maxAmountRupees}
                  onChange={(e) => setMaxAmountRupees(Number(e.target.value))}
                  className="w-full px-3 py-1.5 bg-[#FAFAF9] border border-[#E5E5E5] rounded-md text-xs text-[#171717] focus:outline-none focus:border-[#0D6EFD]"
                />
                <span className="text-[10px] text-[#737373] mt-0.5 block">
                  Hard ceiling for automated recovery.
                </span>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[#171717] mb-1">
                  Human Approval Threshold (₹)
                </label>
                <input
                  type="number"
                  min={100}
                  step={500}
                  value={humanThresholdRupees}
                  onChange={(e) => setHumanThresholdRupees(Number(e.target.value))}
                  className="w-full px-3 py-1.5 bg-[#FAFAF9] border border-[#E5E5E5] rounded-md text-xs text-[#171717] focus:outline-none focus:border-[#0D6EFD]"
                />
                <span className="text-[10px] text-[#737373] mt-0.5 block">
                  Amounts above this are automatically escalated.
                </span>
              </div>
            </div>

            {/* Allowed Actions Checklist */}
            <div className="pt-3 border-t border-[#F0F0F0] space-y-2.5">
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-[#737373]">
                Permitted Recovery Actions
              </label>

              <div className="space-y-2">
                {ALL_ACTIONS.map((action) => {
                  const isChecked = allowedActions.includes(action.id);
                  return (
                    <label
                      key={action.id}
                      className={`p-3 border rounded-lg flex items-start gap-3 cursor-pointer transition-colors ${
                        isChecked ? 'bg-[#EAF2FF]/30 border-[#0D6EFD]/30' : 'bg-[#FAFAF9] border-[#E5E5E5]'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleActionToggle(action.id)}
                        className="mt-0.5 rounded border-[#E5E5E5] text-[#0D6EFD] focus:ring-0"
                      />
                      <div>
                        <span className="font-semibold text-[#171717] block">{action.name}</span>
                        <p className="text-[11px] text-[#737373] mt-0.5">{action.desc}</p>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            <div className="pt-3">
              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#0D6EFD] hover:bg-[#0958D9] text-white rounded-md text-xs font-medium transition-colors shadow-2xs disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{saving ? 'Saving...' : 'Save Safety Policy'}</span>
              </button>
            </div>
          </form>
        </div>

        {/* Right 1 Span: Integration & Environment Status */}
        <div className="space-y-4">
          {/* Razorpay Test Mode Card */}
          <div className="bg-white border border-[#E5E5E5] rounded-xl p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-[#737373]">
                Razorpay Connection
              </span>
              <span className="px-2 py-0.5 bg-[#ECFDF3] text-[#16A34A] border border-[#16A34A]/20 rounded text-[10px] font-semibold">
                CONNECTED
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between text-[#737373]">
                <span>Key ID:</span>
                <span className="font-mono text-[#171717]">rzp_test_TU75••••••••</span>
              </div>
              <div className="flex justify-between text-[#737373]">
                <span>Secret:</span>
                <span className="font-mono text-[#171717]">Configured via .env</span>
              </div>
              <div className="flex justify-between text-[#737373]">
                <span>Mode:</span>
                <span className="font-medium text-[#D97706]">Test Mode</span>
              </div>
            </div>
          </div>

          {/* AI Intelligence Provider Card */}
          <div className="bg-white border border-[#E5E5E5] rounded-xl p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-[#737373]">
                AI Intelligence Engine
              </span>
              <span className="px-2 py-0.5 bg-[#ECFDF3] text-[#16A34A] border border-[#16A34A]/20 rounded text-[10px] font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A]"></span>
                ONLINE
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between text-[#737373]">
                <span>Provider:</span>
                <span className="font-medium text-[#171717]">Ollama (Local)</span>
              </div>
              <div className="flex justify-between text-[#737373]">
                <span>Model:</span>
                <span className="font-mono text-[#0D6EFD] font-medium">qwen3:8b</span>
              </div>
              <div className="flex justify-between text-[#737373]">
                <span>Authority:</span>
                <span className="text-[#57534E]">Advisory Only (Safety Gated)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
