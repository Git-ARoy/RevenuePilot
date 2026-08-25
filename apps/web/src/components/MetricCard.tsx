import React from 'react';

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: {
    value: string;
    isPositive?: boolean;
    isNeutral?: boolean;
  };
  icon?: React.ReactNode;
  highlight?: 'primary' | 'success' | 'warning' | 'neutral';
}

export default function MetricCard({
  title,
  value,
  subtitle,
  trend,
  icon,
  highlight = 'neutral',
}: MetricCardProps) {
  // Border and accent styling based on highlight
  const getHighlightClass = () => {
    switch (highlight) {
      case 'primary':
        return 'border-l-4 border-l-[#0D6EFD]';
      case 'success':
        return 'border-l-4 border-l-[#16A34A]';
      case 'warning':
        return 'border-l-4 border-l-[#D97706]';
      default:
        return '';
    }
  };

  return (
    <div
      className={`bg-white border border-[#E5E5E5] rounded-xl p-5 shadow-xs hover:border-[#D4D4D4] transition-all flex flex-col justify-between ${getHighlightClass()}`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-[#737373]">
          {title}
        </span>
        {icon && <div className="text-[#A3A3A3]">{icon}</div>}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-2xl lg:text-3xl font-semibold tracking-tight text-[#171717]">
          {value}
        </span>
        {trend && (
          <span
            className={`text-[11px] font-medium px-1.5 py-0.5 rounded ${
              trend.isNeutral
                ? 'bg-[#F5F5F4] text-[#737373]'
                : trend.isPositive
                ? 'bg-[#ECFDF3] text-[#16A34A]'
                : 'bg-[#FEF2F2] text-[#DC2626]'
            }`}
          >
            {trend.value}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="text-[11px] text-[#737373] mt-2 pt-2 border-t border-[#F0F0F0]">
          {subtitle}
        </p>
      )}
    </div>
  );
}
