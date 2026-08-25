/**
 * Shared formatting utilities adhering to DESIGN_LANGUAGE.md
 * Financial numbers are first-class UI elements.
 */

export function formatCurrency(paise: number | null | undefined): string {
  if (paise === null || paise === undefined) return '₹0.00';
  const rupees = paise / 100;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(rupees);
}

export function formatCompactCurrency(paise: number | null | undefined): string {
  if (paise === null || paise === undefined || paise === 0) return '₹0';
  const rupees = paise / 100;

  if (rupees >= 10000000) {
    // Crores
    return `₹${(rupees / 10000000).toFixed(2)}Cr`;
  }
  if (rupees >= 100000) {
    // Lakhs
    return `₹${(rupees / 100000).toFixed(2)}L`;
  }
  if (rupees >= 1000) {
    // Thousands
    return `₹${(rupees / 1000).toFixed(1)}k`;
  }
  return `₹${rupees.toFixed(0)}`;
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '0.0%';
  // Check if value is already on 0-100 scale or 0-1 scale
  const percent = value > 1 ? value : value * 100;
  return `${percent.toFixed(1)}%`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '-';
  const date = new Date(iso);
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function formatTimeOnly(iso: string | null | undefined): string {
  if (!iso) return '-';
  const date = new Date(iso);
  return new Intl.DateTimeFormat('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

export function formatRelativeTime(iso: string | null | undefined): string {
  if (!iso) return '-';
  const diffInMs = new Date(iso).getTime() - Date.now();
  const diffInMinutes = Math.round(diffInMs / (1000 * 60));
  const diffInHours = Math.round(diffInMs / (1000 * 60 * 60));
  const diffInDays = Math.round(diffInMs / (1000 * 60 * 60 * 24));

  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
  if (Math.abs(diffInDays) > 0) return rtf.format(diffInDays, 'day');
  if (Math.abs(diffInHours) > 0) return rtf.format(diffInHours, 'hour');
  if (Math.abs(diffInMinutes) > 0) return rtf.format(diffInMinutes, 'minute');
  return 'just now';
}

export interface StatusStyle {
  label: string;
  bg: string;
  text: string;
  border: string;
  dot: string;
}

export function getStatusStyle(status: string | null | undefined): StatusStyle {
  const normalized = (status || '').toUpperCase();

  switch (normalized) {
    case 'RECOVERED':
    case 'PAYMENT_RECONCILED':
    case 'RECOVERY_VERIFIED':
      return {
        label: 'Recovered',
        bg: 'bg-[#ECFDF3]',
        text: 'text-[#16A34A]',
        border: 'border-[#16A34A]/20',
        dot: 'bg-[#16A34A]',
      };

    case 'ACTION_PENDING':
    case 'STRATEGY_SELECTED':
    case 'ELIGIBILITY_CHECKED':
      return {
        label: 'Action Pending',
        bg: 'bg-[#EAF2FF]',
        text: 'text-[#0D6EFD]',
        border: 'border-[#0D6EFD]/20',
        dot: 'bg-[#0D6EFD]',
      };

    case 'WAITING_FOR_OUTCOME':
    case 'ACTION_EXECUTING':
    case 'RETRY_PENDING':
      return {
        label: 'Awaiting Payment',
        bg: 'bg-[#FFF7E6]',
        text: 'text-[#D97706]',
        border: 'border-[#D97706]/20',
        dot: 'bg-[#D97706]',
      };

    case 'ESCALATED':
    case 'CASE_ESCALATED':
      return {
        label: 'Escalated',
        bg: 'bg-[#FEF3C7]',
        text: 'text-[#B45309]',
        border: 'border-[#B45309]/20',
        dot: 'bg-[#B45309]',
      };

    case 'ACTION_FAILED':
    case 'BLOCKED':
    case 'ACTION_BLOCKED':
    case 'TERMINAL':
    case 'FAILED':
      return {
        label: 'Failed',
        bg: 'bg-[#FEF2F2]',
        text: 'text-[#DC2626]',
        border: 'border-[#DC2626]/20',
        dot: 'bg-[#DC2626]',
      };

    case 'STOPPED':
    case 'CASE_STOPPED':
      return {
        label: 'Stopped',
        bg: 'bg-[#F3F4F6]',
        text: 'text-[#6B7280]',
        border: 'border-[#D1D5DB]',
        dot: 'bg-[#9CA3AF]',
      };

    case 'DETECTED':
    case 'DIAGNOSED':
    default:
      return {
        label: normalized || 'Detected',
        bg: 'bg-[#F5F5F4]',
        text: 'text-[#57534E]',
        border: 'border-[#E7E5E4]',
        dot: 'bg-[#A8A29E]',
      };
  }
}
