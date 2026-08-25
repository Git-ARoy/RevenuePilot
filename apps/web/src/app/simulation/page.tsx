'use client';

import React, { useEffect, useState } from 'react';
import { fetchAPI } from '@/lib/api';
import { 
  formatCurrency, 
  formatCompactCurrency, 
  formatPercent, 
  formatDate 
} from '@/lib/format';
import { BatchRun, BatchMetrics } from '@/types';
import StatusBadge from '@/components/StatusBadge';
import MetricCard from '@/components/MetricCard';
import { 
  Play, 
  Layers, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Sliders, 
  Activity, 
  Sparkles, 
  ShieldAlert, 
  HelpCircle 
} from 'lucide-react';

export default function SimulationPage() {
  const [batches, setBatches] = useState<BatchRun[]>([]);
  const [selectedBatch, setSelectedBatch] = useState<BatchRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [runningBatchId, setRunningBatchId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Generator form state
  const [seed, setSeed] = useState<number>(42);
  const [count, setCount] = useState<number>(100);
  const [amountMin, setAmountMin] = useState<number>(10000);  // ₹100 in paise
  const [amountMax, setAmountMax] = useState<number>(300000); // ₹3,000 in paise

  // Scenario mix percentages
  const [mix, setMix] = useState({
    transient_failure: 0.25,
    insufficient_funds: 0.20,
    payment_method_failure: 0.15,
    bank_decline: 0.10,
    checkout_abandonment: 0.10,
    already_recovered: 0.10,
    non_recoverable: 0.05,
    ambiguous: 0.05,
  });

  const loadBatches = async () => {
    try {
      setLoading(true);
      const res = await fetchAPI<BatchRun[]>('/api/simulation/batches');
      setBatches(res || []);
      if (res && res.length > 0) {
        setSelectedBatch(res[0]);
      }
    } catch (err: any) {
      console.error('Error fetching batches:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBatches();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setGenerating(true);
      setError(null);
      setMessage(null);

      const res = await fetchAPI<{ batch_id: string; case_count: number; batch: BatchRun }>(
        '/api/simulation/generate',
        {
          method: 'POST',
          body: JSON.stringify({
            seed,
            count,
            amount_min: amountMin,
            amount_max: amountMax,
            scenario_mix: mix,
          }),
        }
      );

      setMessage(`Synthetic batch with ${res.case_count} cases created successfully.`);
      await loadBatches();
      setSelectedBatch(res.batch);
    } catch (err: any) {
      setError(err.message || 'Batch generation failed.');
    } finally {
      setGenerating(false);
    }
  };

  const handleRunBatch = async (batchId: string) => {
    try {
      setRunningBatchId(batchId);
      setError(null);
      setMessage(null);

      const res = await fetchAPI<{ batch_id: string; status: string; metrics: BatchMetrics }>(
        `/api/simulation/batches/${batchId}/run`,
        {
          method: 'POST',
          body: JSON.stringify({ mode: 'FULL_AGENT' }),
        }
      );

      setMessage(`Agent batch evaluation completed. Recovery Rate: ${res.metrics.recovery_rate}%`);
      await loadBatches();
      
      const updated = await fetchAPI<BatchRun>(`/api/simulation/batches/${batchId}`);
      setSelectedBatch(updated);
    } catch (err: any) {
      setError(err.message || 'Failed to run batch evaluation.');
    } finally {
      setRunningBatchId(null);
    }
  };

  const latestMetrics = selectedBatch?.metrics;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header with Mode indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#E5E5E5]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-semibold tracking-tight text-[#171717]">
              Evaluation & Simulation Engine
            </h1>
            <span className="px-2 py-0.5 bg-[#FFF7E6] text-[#D97706] border border-[#D97706]/20 rounded text-[11px] font-semibold">
              SIMULATION MODE
            </span>
          </div>
          <p className="text-xs text-[#737373]">
            Deterministic evaluation engine with seeded scenarios for reproducible recovery benchmark testing.
          </p>
        </div>

        <button
          onClick={loadBatches}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-[#FAFAF9] text-[#171717] border border-[#E5E5E5] rounded-md text-xs font-medium transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5 text-[#737373]" />
          <span>Refresh Batches</span>
        </button>
      </div>

      {/* Notifications */}
      {message && (
        <div className="p-3 bg-[#ECFDF3] border border-[#16A34A]/30 rounded-lg text-xs text-[#16A34A] flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{message}</span>
        </div>
      )}
      {error && (
        <div className="p-3 bg-[#FEF2F2] border border-[#DC2626]/30 rounded-lg text-xs text-[#DC2626] flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Evaluation Results Banner (if batch selected) */}
      {selectedBatch && (
        <div className="bg-white border border-[#E5E5E5] rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-[#F0F0F0]">
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-[#171717]">
                Batch Evaluation #{selectedBatch.id.slice(0, 8)}
              </span>
              <StatusBadge status={selectedBatch.status} />
              <span className="text-[11px] font-mono text-[#737373] bg-[#FAFAF9] px-2 py-0.5 rounded border border-[#E5E5E5]">
                Seed: {selectedBatch.seed}
              </span>
            </div>

            {selectedBatch.status !== 'COMPLETED' && (
              <button
                onClick={() => handleRunBatch(selectedBatch.id)}
                disabled={runningBatchId === selectedBatch.id}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#0D6EFD] hover:bg-[#0958D9] text-white rounded-md text-xs font-medium transition-colors disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{runningBatchId === selectedBatch.id ? 'Evaluating...' : 'Run Full Agent Evaluation'}</span>
              </button>
            )}
          </div>

          {/* Metrics KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[#FAFAF9] border border-[#E5E5E5] rounded-lg p-3.5">
              <span className="text-[10px] font-semibold uppercase text-[#737373]">Cases Evaluated</span>
              <p className="text-2xl font-semibold text-[#171717] mt-1">{selectedBatch.case_count}</p>
            </div>

            <div className="bg-[#FAFAF9] border border-[#E5E5E5] rounded-lg p-3.5">
              <span className="text-[10px] font-semibold uppercase text-[#737373]">Amount at Risk</span>
              <p className="text-2xl font-semibold text-[#171717] mt-1">
                {formatCompactCurrency(selectedBatch.amount_at_risk)}
              </p>
              <span className="text-[10px] text-[#737373]">{formatCurrency(selectedBatch.amount_at_risk)}</span>
            </div>

            <div className="bg-[#FAFAF9] border border-[#E5E5E5] rounded-lg p-3.5">
              <span className="text-[10px] font-semibold uppercase text-[#16A34A]">Revenue Recovered</span>
              <p className="text-2xl font-semibold text-[#16A34A] mt-1">
                {formatCompactCurrency(selectedBatch.amount_recovered)}
              </p>
              <span className="text-[10px] text-[#737373]">{formatCurrency(selectedBatch.amount_recovered)}</span>
            </div>

            <div className="bg-[#FAFAF9] border border-[#E5E5E5] rounded-lg p-3.5">
              <span className="text-[10px] font-semibold uppercase text-[#0D6EFD]">Recovery Rate</span>
              <p className="text-2xl font-semibold text-[#0D6EFD] mt-1">
                {formatPercent(selectedBatch.recovery_rate)}
              </p>
              <span className="text-[10px] text-[#737373]">Net captured</span>
            </div>
          </div>

          {/* Detailed Outcomes Grid */}
          {latestMetrics && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs">
              <div className="p-3 bg-white border border-[#E5E5E5] rounded-lg">
                <span className="text-[#737373]">Actions Attempted:</span>
                <span className="font-semibold text-[#171717] ml-1.5">{latestMetrics.actions_attempted || 0}</span>
              </div>
              <div className="p-3 bg-white border border-[#E5E5E5] rounded-lg">
                <span className="text-[#737373]">Verified Recoveries:</span>
                <span className="font-semibold text-[#16A34A] ml-1.5">{latestMetrics.recovered_cases || 0}</span>
              </div>
              <div className="p-3 bg-white border border-[#E5E5E5] rounded-lg">
                <span className="text-[#737373]">Escalations:</span>
                <span className="font-semibold text-[#D97706] ml-1.5">{latestMetrics.escalations || 0}</span>
              </div>
              <div className="p-3 bg-white border border-[#E5E5E5] rounded-lg">
                <span className="text-[#737373]">Terminal Failures:</span>
                <span className="font-semibold text-[#DC2626] ml-1.5">{latestMetrics.terminal_failures || 0}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Two Column Section: Scenario Generator & Previous Batches */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left: Generator Panel */}
        <div className="bg-white border border-[#E5E5E5] rounded-xl p-5 shadow-xs space-y-4">
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[#737373]">
              Generate Synthetic Batch
            </h2>
            <p className="text-[11px] text-[#737373] mt-0.5">
              Create deterministic test cases to evaluate agent recovery decisions.
            </p>
          </div>

          <form onSubmit={handleGenerate} className="space-y-3.5 text-xs">
            <div>
              <label className="block text-[11px] font-medium text-[#171717] mb-1">
                Deterministic Random Seed
              </label>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value))}
                className="w-full px-3 py-1.5 bg-[#FAFAF9] border border-[#E5E5E5] rounded-md text-xs text-[#171717] focus:outline-none focus:border-[#0D6EFD]"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[11px] font-medium text-[#171717] mb-1">
                  Case Count
                </label>
                <input
                  type="number"
                  value={count}
                  min={10}
                  max={500}
                  onChange={(e) => setCount(Number(e.target.value))}
                  className="w-full px-3 py-1.5 bg-[#FAFAF9] border border-[#E5E5E5] rounded-md text-xs text-[#171717] focus:outline-none focus:border-[#0D6EFD]"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[#171717] mb-1">
                  Amount Range
                </label>
                <div className="text-[11px] text-[#737373] pt-2">
                  ₹{amountMin / 100} - ₹{amountMax / 100}
                </div>
              </div>
            </div>

            {/* Scenario Mix Distribution */}
            <div className="pt-2 border-t border-[#F0F0F0] space-y-2">
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-[#737373]">
                Scenario Distribution
              </label>

              <div className="space-y-1.5 text-[11px]">
                <div className="flex justify-between text-[#57534E]">
                  <span>Transient Failures:</span>
                  <span className="font-mono">{Math.round(mix.transient_failure * 100)}%</span>
                </div>
                <div className="flex justify-between text-[#57534E]">
                  <span>Insufficient Funds:</span>
                  <span className="font-mono">{Math.round(mix.insufficient_funds * 100)}%</span>
                </div>
                <div className="flex justify-between text-[#57534E]">
                  <span>Payment Method Failure:</span>
                  <span className="font-mono">{Math.round(mix.payment_method_failure * 100)}%</span>
                </div>
                <div className="flex justify-between text-[#57534E]">
                  <span>Bank Declines:</span>
                  <span className="font-mono">{Math.round(mix.bank_decline * 100)}%</span>
                </div>
                <div className="flex justify-between text-[#57534E]">
                  <span>Checkout Abandonment:</span>
                  <span className="font-mono">{Math.round(mix.checkout_abandonment * 100)}%</span>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={generating}
              className="w-full py-2.5 bg-[#0D6EFD] hover:bg-[#0958D9] text-white rounded-md text-xs font-medium transition-colors shadow-2xs disabled:opacity-50"
            >
              {generating ? 'Synthesizing...' : 'Generate 100-Case Evaluation Batch'}
            </button>
          </form>
        </div>

        {/* Right: Previous Batches List */}
        <div className="lg:col-span-2 bg-white border border-[#E5E5E5] rounded-xl p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[#737373]">
              Evaluation History
            </h2>
            <span className="text-[11px] text-[#A3A3A3]">{batches.length} batches recorded</span>
          </div>

          <div className="divide-y divide-[#F0F0F0] border border-[#E5E5E5] rounded-lg overflow-hidden">
            {batches.length === 0 ? (
              <div className="py-8 text-center text-[#737373] text-xs">
                No simulation batches generated yet. Click "Generate Batch" to create one.
              </div>
            ) : (
              batches.map((b) => (
                <div
                  key={b.id}
                  onClick={() => setSelectedBatch(b)}
                  className={`p-3.5 flex items-center justify-between cursor-pointer transition-colors ${
                    selectedBatch?.id === b.id ? 'bg-[#EAF2FF]/40' : 'hover:bg-[#FAFAF9]'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-[#171717]">
                        #{b.id.slice(0, 8)}
                      </span>
                      <StatusBadge status={b.status} />
                      <span className="text-[11px] text-[#737373]">
                        {b.case_count} cases
                      </span>
                    </div>
                    <div className="text-[11px] text-[#737373]">
                      At Risk: {formatCurrency(b.amount_at_risk)} &bull; Recovered:{' '}
                      <span className="text-[#16A34A] font-medium">{formatCurrency(b.amount_recovered)}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <span className="text-[10px] uppercase font-semibold text-[#737373]">Rate</span>
                      <p className="font-mono text-xs font-bold text-[#0D6EFD]">
                        {formatPercent(b.recovery_rate)}
                      </p>
                    </div>

                    {b.status !== 'COMPLETED' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRunBatch(b.id);
                        }}
                        disabled={runningBatchId === b.id}
                        className="px-2.5 py-1 bg-[#0D6EFD] text-white rounded text-[11px] font-medium"
                      >
                        {runningBatchId === b.id ? 'Running...' : 'Run'}
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
