'use client';

import React, { useState } from 'react';
import { AuditEvent } from '@/types';
import { formatDate, formatTimeOnly, formatCurrency } from '@/lib/format';
import { 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Clock, 
  Send, 
  ShieldAlert, 
  Cpu, 
  User, 
  Zap, 
  ChevronDown, 
  ChevronRight 
} from 'lucide-react';

interface TimelineProps {
  events: AuditEvent[];
}

export default function Timeline({ events }: TimelineProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const getEventVisuals = (eventType: string) => {
    switch (eventType) {
      case 'RECOVERY_VERIFIED':
      case 'PAYMENT_RECONCILED':
        return {
          icon: CheckCircle2,
          color: 'text-[#16A34A]',
          bg: 'bg-[#ECFDF3]',
          border: 'border-[#16A34A]/30',
          title: 'Revenue Verified',
        };
      case 'ACTION_EXECUTED':
        return {
          icon: Send,
          color: 'text-[#0D6EFD]',
          bg: 'bg-[#EAF2FF]',
          border: 'border-[#0D6EFD]/30',
          title: 'Action Executed',
        };
      case 'ACTION_PROPOSED':
        return {
          icon: Cpu,
          color: 'text-[#0D6EFD]',
          bg: 'bg-[#EAF2FF]',
          border: 'border-[#0D6EFD]/30',
          title: 'Strategy Selected',
        };
      case 'ACTION_BLOCKED':
        return {
          icon: ShieldAlert,
          color: 'text-[#DC2626]',
          bg: 'bg-[#FEF2F2]',
          border: 'border-[#DC2626]/30',
          title: 'Action Blocked by Policy',
        };
      case 'CASE_ESCALATED':
        return {
          icon: AlertTriangle,
          color: 'text-[#D97706]',
          bg: 'bg-[#FFF7E6]',
          border: 'border-[#D97706]/30',
          title: 'Escalated to Human',
        };
      case 'CASE_DIAGNOSED':
        return {
          icon: Clock,
          color: 'text-[#57534E]',
          bg: 'bg-[#F5F5F4]',
          border: 'border-[#E7E5E4]',
          title: 'Failure Diagnosed',
        };
      case 'CASE_DETECTED':
      default:
        return {
          icon: Zap,
          color: 'text-[#57534E]',
          bg: 'bg-[#F5F5F4]',
          border: 'border-[#E7E5E4]',
          title: 'Case Detected',
        };
    }
  };

  const getActorBadge = (actorType: string) => {
    switch ((actorType || '').toUpperCase()) {
      case 'AGENT':
        return <span className="px-1.5 py-0.5 bg-[#EAF2FF] text-[#0D6EFD] rounded text-[10px] font-medium">AGENT</span>;
      case 'SYSTEM':
        return <span className="px-1.5 py-0.5 bg-[#F5F5F4] text-[#57534E] rounded text-[10px] font-medium">SYSTEM</span>;
      case 'MERCHANT':
        return <span className="px-1.5 py-0.5 bg-[#FFF7E6] text-[#D97706] rounded text-[10px] font-medium">MERCHANT</span>;
      case 'RAZORPAY_WEBHOOK':
        return <span className="px-1.5 py-0.5 bg-[#ECFDF3] text-[#16A34A] rounded text-[10px] font-medium">WEBHOOK</span>;
      default:
        return <span className="px-1.5 py-0.5 bg-[#F5F5F4] text-[#737373] rounded text-[10px] font-medium">{actorType}</span>;
    }
  };

  if (events.length === 0) {
    return (
      <div className="py-8 text-center text-[#737373] text-xs">
        No audit events recorded yet.
      </div>
    );
  }

  return (
    <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-[1px] before:bg-[#E5E5E5]">
      {events.map((event) => {
        const visual = getEventVisuals(event.event_type);
        const Icon = visual.icon;
        const isExpanded = expandedId === event.id;
        const meta = event.metadata || {};

        return (
          <div key={event.id} className="relative group">
            {/* Timeline Dot / Icon */}
            <div
              className={`absolute -left-6 top-0.5 w-5 h-5 rounded-full ${visual.bg} ${visual.border} border flex items-center justify-center`}
            >
              <Icon className={`w-3 h-3 ${visual.color}`} />
            </div>

            {/* Event Content */}
            <div className="bg-white border border-[#E5E5E5] rounded-lg p-3.5 shadow-2xs hover:border-[#D4D4D4] transition-all">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-xs text-[#171717]">
                    {visual.title}
                  </span>
                  {getActorBadge(event.actor_type)}
                </div>
                <time className="text-[11px] text-[#A3A3A3] shrink-0 font-mono">
                  {formatTimeOnly(event.created_at)}
                </time>
              </div>

              {/* Event Description Summary */}
              <div className="mt-1.5 text-xs text-[#57534E]">
                {event.event_type === 'RECOVERY_VERIFIED' && (
                  <p className="font-medium text-[#16A34A]">
                    Payment captured successfully. Recovery verified.
                  </p>
                )}
                {event.event_type === 'ACTION_EXECUTED' && (
                  <p>
                    Executed <span className="font-semibold text-[#171717]">{meta.action_type || 'Action'}</span>
                    {meta.external_reference ? ` (Ref: ${meta.external_reference})` : ''}.
                  </p>
                )}
                {event.event_type === 'ACTION_BLOCKED' && (
                  <p className="text-[#DC2626] font-medium">
                    Blocked reason: {meta.block_reason || meta.reason || 'Policy constraint'}
                  </p>
                )}
                {event.event_type === 'CASE_DIAGNOSED' && (
                  <p>
                    Root cause classified as <span className="font-semibold text-[#171717]">{meta.code || 'Diagnosis'}</span>.
                  </p>
                )}
                {event.event_type === 'ACTION_PROPOSED' && (
                  <p>
                    Strategy recommended: <span className="font-semibold text-[#171717]">{meta.action || meta.action_type || 'Action'}</span>.
                  </p>
                )}
                {event.event_type === 'CASE_ESCALATED' && (
                  <p className="text-[#D97706]">
                    Escalation reason: {meta.reason || meta.reason_code || 'Manual intervention needed'}
                  </p>
                )}
                {event.event_type === 'CASE_DETECTED' && (
                  <p>Opportunity detected from payment failure.</p>
                )}
              </div>

              {/* Collapsible Metadata */}
              {meta && Object.keys(meta).length > 0 && (
                <div className="mt-2 pt-2 border-t border-[#F0F0F0]">
                  <button
                    onClick={() => toggleExpand(event.id)}
                    className="flex items-center gap-1 text-[11px] text-[#737373] hover:text-[#171717] font-medium transition-colors"
                  >
                    {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                    <span>{isExpanded ? 'Hide event payload' : 'Inspect payload'}</span>
                  </button>

                  {isExpanded && (
                    <pre className="mt-2 p-2.5 bg-[#FAFAF9] border border-[#E5E5E5] rounded text-[11px] text-[#171717] overflow-x-auto font-mono">
                      {JSON.stringify(meta, null, 2)}
                    </pre>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
