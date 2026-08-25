'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Layers, 
  FlaskConical, 
  ShieldCheck, 
  Zap, 
  ExternalLink 
} from 'lucide-react';

const mainNav = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Recovery Cases', href: '/cases', icon: Layers },
];

const secondaryNav = [
  { name: 'Evaluation & Simulation', href: '/simulation', icon: FlaskConical },
  { name: 'Safety Policies', href: '/policies', icon: ShieldCheck },
];

export default function Sidebar() {
  const pathname = usePathname();

  const isLinkActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <aside className="w-60 bg-white border-r border-[#E5E5E5] flex flex-col h-full shrink-0 select-none">
      {/* Brand Header */}
      <div className="h-14 px-5 border-b border-[#E5E5E5] flex items-center gap-2.5">
        <div className="w-7 h-7 rounded bg-[#0D6EFD] text-white flex items-center justify-center font-bold text-xs shadow-sm">
          RP
        </div>
        <div>
          <h1 className="text-sm font-semibold tracking-tight text-[#171717]">
            RevenuePilot
          </h1>
          <p className="text-[10px] text-[#737373] tracking-wide uppercase font-medium">
            Recovery Agent
          </p>
        </div>
      </div>

      {/* Nav List */}
      <div className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
        {/* Operations Section */}
        <div>
          <p className="px-3 text-[11px] font-semibold tracking-wider text-[#A3A3A3] uppercase mb-1.5">
            Operations
          </p>
          <nav className="space-y-0.5">
            {mainNav.map((item) => {
              const active = isLinkActive(item.href);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                    active
                      ? 'bg-[#EAF2FF] text-[#0D6EFD]'
                      : 'text-[#737373] hover:text-[#171717] hover:bg-[#F5F5F4]'
                  }`}
                >
                  <item.icon className={`w-4 h-4 ${active ? 'text-[#0D6EFD]' : 'text-[#737373]'}`} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Engine & Governance Section */}
        <div>
          <p className="px-3 text-[11px] font-semibold tracking-wider text-[#A3A3A3] uppercase mb-1.5">
            Intelligence & Safety
          </p>
          <nav className="space-y-0.5">
            {secondaryNav.map((item) => {
              const active = isLinkActive(item.href);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                    active
                      ? 'bg-[#EAF2FF] text-[#0D6EFD]'
                      : 'text-[#737373] hover:text-[#171717] hover:bg-[#F5F5F4]'
                  }`}
                >
                  <item.icon className={`w-4 h-4 ${active ? 'text-[#0D6EFD]' : 'text-[#737373]'}`} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-[#E5E5E5] bg-[#FAFAF9] m-2 rounded-lg border">
        <div className="flex items-center justify-between text-[11px] text-[#737373]">
          <span className="flex items-center gap-1 font-medium text-[#171717]">
            <Zap className="w-3 h-3 text-[#0D6EFD]" />
            Razorpay Integration
          </span>
          <span className="text-[10px] bg-[#EAF2FF] text-[#0D6EFD] px-1.5 py-0.5 rounded font-mono font-medium">
            v1.0
          </span>
        </div>
        <p className="text-[10px] text-[#737373] mt-1">
          Autonomous recovery engine with deterministic safety gates.
        </p>
      </div>
    </aside>
  );
}
