'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { ShieldCheck, Activity, Terminal } from 'lucide-react';

export default function TopBar() {
  const pathname = usePathname();

  // Generate breadcrumb title
  const getBreadcrumbs = () => {
    if (pathname === '/') return ['Overview'];
    if (pathname.startsWith('/cases/')) return ['Recovery', 'Case Investigation'];
    if (pathname.startsWith('/cases')) return ['Recovery', 'Active Cases'];
    if (pathname.startsWith('/simulation')) return ['Evaluation', 'Batch Simulation'];
    if (pathname.startsWith('/policies')) return ['Settings', 'Safety Policies'];
    return ['Dashboard'];
  };

  const crumbs = getBreadcrumbs();

  return (
    <header className="h-14 bg-white border-b border-[#E5E5E5] px-6 flex items-center justify-between shrink-0 z-10">
      {/* Left: Breadcrumbs */}
      <div className="flex items-center gap-2 text-xs">
        <span className="font-semibold text-[#171717]">RevenuePilot</span>
        {crumbs.map((crumb, idx) => (
          <React.Fragment key={crumb}>
            <span className="text-[#A3A3A3]">/</span>
            <span className={idx === crumbs.length - 1 ? 'font-medium text-[#171717]' : 'text-[#737373]'}>
              {crumb}
            </span>
          </React.Fragment>
        ))}
      </div>

      {/* Right: Operational Status Controls */}
      <div className="flex items-center gap-3">
        {/* Test Mode / Simulation Mode Indicator */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[#FFF7E6] border border-[#D97706]/20 rounded-md text-xs font-medium text-[#D97706]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#D97706] animate-pulse"></span>
          <span>TEST MODE</span>
        </div>

        {/* Local AI Engine Status */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-[#F5F5F4] border border-[#E7E5E4] rounded-md text-xs text-[#57534E]">
          <Activity className="w-3.5 h-3.5 text-[#16A34A]" />
          <span>Ollama Qwen3 8B</span>
        </div>

        {/* Merchant Account Badge */}
        <div className="flex items-center gap-2 pl-2 border-l border-[#E5E5E5] text-xs">
          <div className="w-6 h-6 rounded bg-[#EAF2FF] text-[#0D6EFD] font-semibold flex items-center justify-center text-[11px]">
            RZ
          </div>
          <span className="font-medium text-[#171717] hidden md:inline">Default Merchant</span>
        </div>
      </div>
    </header>
  );
}
