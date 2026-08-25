'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { fetchAPI } from '@/lib/api';
import { 
  formatCurrency, 
  formatCompactCurrency, 
  formatPercent, 
  formatRelativeTime 
} from '@/lib/format';
import { DashboardSummary, RecoveryCase } from '@/types';
import MetricCard from '@/components/MetricCard';
import StatusBadge from '@/components/StatusBadge';
import DataTable, { Column } from '@/components/DataTable';
import { 
  ArrowUpRight, 
  Play, 
  Layers, 
  AlertCircle, 
  TrendingUp, 
  ShieldCheck, 
  RefreshCw, 
  CheckCircle2 
} from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [recentCases, setRecentCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [summaryData, casesData] = await Promise.all([
        fetchAPI<DashboardSummary>('/api/dashboard/summary'),
        fetchAPI<any>('/api/recovery-cases?page_size=10')
      ]);
      setSummary(summaryData || null);
      setRecentCases(casesData?.items || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const columns: Column<RecoveryCase>[] = [
    {
      header: 'Case ID',
      cell: (item) => (
        <span className="font-mono text-[11px] font-medium text-[#171717]">
          #{item.id.slice(0, 8)}
        </span>
      ),
    },
    {
      header: 'Type',
      cell: (item) => (
        <span className="text-xs text-[#57534E]">
          {item.case_type?.replace(/_/g, ' ') || 'Payment Failure'}
        </span>
      ),
    },
    {
      header: 'Amount at Risk',
      cell: (item) => (
        <span className="font-semibold text-xs text-[#171717]">
          {formatCurrency(item.amount_at_risk)}
        </span>
      ),
    },
    {
      header: 'Diagnosis / Reason',
      cell: (item) => (
        <span className="text-xs text-[#737373] line-clamp-1 max-w-[200px]">
          {item.diagnosis_code?.replace(/_/g, ' ') || 'Awaiting analysis'}
        </span>
      ),
    },
    {
      header: 'Score',
      cell: (item) => {
        if (item.recovery_score === null || item.recovery_score === undefined) return <span className="text-[#A3A3A3]">-</span>;
        const scoreVal = Math.round((item.recovery_score > 1 ? item.recovery_score : item.recovery_score * 100));
        return (
          <span className={`font-mono text-xs font-semibold ${scoreVal >= 60 ? 'text-[#16A34A]' : scoreVal >= 30 ? 'text-[#D97706]' : 'text-[#737373]'}`}>
            {scoreVal}%
          </span>
        );
      },
    },
    {
      header: 'Action Strategy',
      cell: (item) => (
        <span className="text-[11px] font-medium text-[#0D6EFD] bg-[#EAF2FF] px-2 py-0.5 rounded">
          {item.current_strategy?.replace(/_/g, ' ') || 'Pending'}
        </span>
      ),
    },
    {
      header: 'Status',
      cell: (item) => <StatusBadge status={item.status} />,
    },
    {
      header: 'Detected',
      cell: (item) => (
        <span className="text-[11px] text-[#A3A3A3]">
          {formatRelativeTime(item.created_at)}
        </span>
      ),
    },
  ];

  if (error) {
    return (
      <div className="bg-white border border-[#E5E5E5] rounded-xl p-8 text-center max-w-lg mx-auto mt-12 shadow-xs">
        <div className="w-12 h-12 rounded-full bg-[#FEF2F2] text-[#DC2626] flex items-center justify-center mx-auto mb-4">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h2 className="text-base font-semibold text-[#171717] mb-1">
          Operational Connection Error
        </h2>
        <p className="text-xs text-[#737373] mb-5">
          {error}
        </p>
        <button
          onClick={loadData}
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#0D6EFD] hover:bg-[#0958D9] text-white rounded-md text-xs font-medium transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Connection</span>
        </button>
      </div>
    );
  }

  const atRisk = summary?.amount_at_risk || 0;
  const recovered = summary?.amount_recovered || 0;
  const recoveryRate = summary?.recovery_rate || 0;

  return (
    <div className="space-y-6">
      {/* 1. Header with Operational Context & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#E5E5E5]">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-[#171717]">
            Revenue Recovery
          </h1>
          <p className="text-xs text-[#737373] mt-0.5">
            Recover more revenue from failed payments without increasing manual operations.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            href="/simulation"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-[#0D6EFD] hover:bg-[#0958D9] text-white rounded-md text-xs font-medium transition-colors shadow-2xs"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Run Evaluation</span>
          </Link>

          <Link
            href="/cases"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-[#FAFAF9] text-[#171717] border border-[#E5E5E5] rounded-md text-xs font-medium transition-colors"
          >
            <Layers className="w-3.5 h-3.5 text-[#737373]" />
            <span>View Active Cases</span>
          </Link>
        </div>
      </div>

      {/* 2. Primary Financial KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Revenue at Risk"
          value={loading ? '...' : formatCompactCurrency(atRisk)}
          subtitle={loading ? undefined : `Exact: ${formatCurrency(atRisk)} detected`}
          highlight="neutral"
        />

        <MetricCard
          title="Revenue Recovered"
          value={loading ? '...' : formatCompactCurrency(recovered)}
          subtitle={loading ? undefined : `Exact: ${formatCurrency(recovered)} captured`}
          highlight="success"
          trend={{
            value: 'Verified',
            isPositive: true,
          }}
        />

        <MetricCard
          title="Recovery Rate"
          value={loading ? '...' : formatPercent(recoveryRate)}
          subtitle="Net financial capture percentage"
          highlight="primary"
        />
      </div>

      {/* 3. Secondary Operational Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-[#E5E5E5] rounded-xl p-4 flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[#737373]">
              Active Opportunities
            </p>
            <p className="text-xl font-semibold text-[#171717] mt-0.5">
              {loading ? '...' : summary?.active_cases || 0}
            </p>
          </div>
          <span className="w-2.5 h-2.5 rounded-full bg-[#0D6EFD]"></span>
        </div>

        <div className="bg-white border border-[#E5E5E5] rounded-xl p-4 flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[#737373]">
              Escalated to Human
            </p>
            <p className="text-xl font-semibold text-[#171717] mt-0.5">
              {loading ? '...' : summary?.escalated_cases || 0}
            </p>
          </div>
          <span className="w-2.5 h-2.5 rounded-full bg-[#D97706]"></span>
        </div>

        <div className="bg-white border border-[#E5E5E5] rounded-xl p-4 flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[#737373]">
              Failed Actions
            </p>
            <p className="text-xl font-semibold text-[#171717] mt-0.5">
              {loading ? '...' : summary?.failed_actions || 0}
            </p>
          </div>
          <span className="w-2.5 h-2.5 rounded-full bg-[#DC2626]"></span>
        </div>
      </div>

      {/* 4. Recent Recovery Opportunities Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-[#171717]">
              Recent Recovery Opportunities
            </h2>
            <p className="text-[11px] text-[#737373]">
              Live payment recovery pipeline governed by deterministic safety policy.
            </p>
          </div>
          <Link
            href="/cases"
            className="text-xs font-medium text-[#0D6EFD] hover:text-[#0958D9] flex items-center gap-1"
          >
            <span>View all cases</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <DataTable
          columns={columns}
          data={recentCases}
          loading={loading}
          onRowClick={(item) => router.push(`/cases/${item.id}`)}
          emptyMessage="No recovery cases detected. Run a simulation batch or trigger test transactions to populate."
        />
      </div>
    </div>
  );
}
