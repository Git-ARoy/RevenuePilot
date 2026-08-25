'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { fetchAPI } from '@/lib/api';
import { formatCurrency, formatRelativeTime } from '@/lib/format';
import { RecoveryCase, PaginatedCasesResponse } from '@/types';
import StatusBadge from '@/components/StatusBadge';
import DataTable, { Column } from '@/components/DataTable';
import { 
  Search, 
  Filter, 
  ChevronLeft, 
  ChevronRight, 
  RefreshCw, 
  Layers 
} from 'lucide-react';

export default function CasesPage() {
  const router = useRouter();
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const loadCases = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('page_size', String(pageSize));
      if (statusFilter) params.set('status', statusFilter);
      if (typeFilter) params.set('case_type', typeFilter);

      const res = await fetchAPI<PaginatedCasesResponse>(`/api/recovery-cases?${params.toString()}`);
      setCases(res?.items || []);
      setTotal(res?.total || 0);
    } catch (err) {
      console.error('Error fetching cases:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, [page, statusFilter, typeFilter]);

  // Client-side search filter
  const filteredCases = cases.filter((c) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.id.toLowerCase().includes(q) ||
      (c.diagnosis_code && c.diagnosis_code.toLowerCase().includes(q)) ||
      (c.case_type && c.case_type.toLowerCase().includes(q))
    );
  });

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
      header: 'Opportunity Type',
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
      header: 'Diagnosis',
      cell: (item) => (
        <span className="text-xs text-[#737373]">
          {item.diagnosis_code ? item.diagnosis_code.replace(/_/g, ' ') : 'Awaiting analysis'}
        </span>
      ),
    },
    {
      header: 'Recovery Score',
      cell: (item) => {
        if (item.recovery_score === null || item.recovery_score === undefined) return <span className="text-[#A3A3A3]">-</span>;
        const scoreVal = Math.round(item.recovery_score > 1 ? item.recovery_score : item.recovery_score * 100);
        return (
          <span className={`font-mono text-xs font-semibold ${scoreVal >= 60 ? 'text-[#16A34A]' : scoreVal >= 30 ? 'text-[#D97706]' : 'text-[#737373]'}`}>
            {scoreVal}%
          </span>
        );
      },
    },
    {
      header: 'Strategy',
      cell: (item) => (
        <span className="text-[11px] font-medium text-[#0D6EFD] bg-[#EAF2FF] px-2 py-0.5 rounded">
          {item.current_strategy?.replace(/_/g, ' ') || 'Pending'}
        </span>
      ),
    },
    {
      header: 'Attempts',
      cell: (item) => (
        <span className="font-mono text-xs text-[#737373]">
          {item.attempt_count} / {item.max_attempts}
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

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#E5E5E5]">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-[#171717]">
            Recovery Cases
          </h1>
          <p className="text-xs text-[#737373] mt-0.5">
            Real-time pipeline of failed transactions and recovery decisions.
          </p>
        </div>

        <button
          onClick={loadCases}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-[#FAFAF9] text-[#171717] border border-[#E5E5E5] rounded-md text-xs font-medium transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5 text-[#737373]" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white border border-[#E5E5E5] rounded-xl p-3.5 flex flex-col md:flex-row gap-3 items-center justify-between shadow-2xs">
        {/* Search */}
        <div className="relative w-full md:w-72">
          <Search className="w-3.5 h-3.5 text-[#A3A3A3] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by case ID or keyword..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8.5 pr-3 py-1.5 bg-[#FAFAF9] border border-[#E5E5E5] rounded-md text-xs text-[#171717] placeholder:text-[#A3A3A3] focus:outline-none focus:border-[#0D6EFD]"
          />
        </div>

        {/* Dropdowns */}
        <div className="flex items-center gap-2.5 w-full md:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-[#737373]">
            <Filter className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Filters:</span>
          </div>

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1.5 bg-[#FAFAF9] border border-[#E5E5E5] rounded-md text-xs text-[#171717] focus:outline-none focus:border-[#0D6EFD]"
          >
            <option value="">All Statuses</option>
            <option value="DETECTED">Detected</option>
            <option value="DIAGNOSED">Diagnosed</option>
            <option value="ACTION_PENDING">Action Pending</option>
            <option value="WAITING_FOR_OUTCOME">Awaiting Payment</option>
            <option value="RECOVERED">Recovered</option>
            <option value="ESCALATED">Escalated</option>
            <option value="STOPPED">Stopped</option>
            <option value="TERMINAL">Failed</option>
          </select>

          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1.5 bg-[#FAFAF9] border border-[#E5E5E5] rounded-md text-xs text-[#171717] focus:outline-none focus:border-[#0D6EFD]"
          >
            <option value="">All Types</option>
            <option value="FAILED_PAYMENT">Failed Payment</option>
            <option value="REPEATED_FAILURE">Repeated Failure</option>
            <option value="ABANDONED_CHECKOUT">Abandoned Checkout</option>
            <option value="FAILED_RECURRING">Failed Recurring</option>
          </select>
        </div>
      </div>

      {/* Cases Table */}
      <DataTable
        columns={columns}
        data={filteredCases}
        loading={loading}
        onRowClick={(item) => router.push(`/cases/${item.id}`)}
        emptyMessage="No recovery cases matching your search criteria."
      />

      {/* Pagination Controls */}
      <div className="flex items-center justify-between text-xs text-[#737373] px-1">
        <span>
          Showing <span className="font-semibold text-[#171717]">{filteredCases.length}</span> of{' '}
          <span className="font-semibold text-[#171717]">{total}</span> total cases
        </span>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1 || loading}
            className="p-1.5 bg-white border border-[#E5E5E5] rounded-md hover:bg-[#FAFAF9] disabled:opacity-40 disabled:cursor-not-allowed text-[#171717]"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <span className="font-medium text-[#171717]">
            Page {page} of {totalPages}
          </span>

          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages || loading}
            className="p-1.5 bg-white border border-[#E5E5E5] rounded-md hover:bg-[#FAFAF9] disabled:opacity-40 disabled:cursor-not-allowed text-[#171717]"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
