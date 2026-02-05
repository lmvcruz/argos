/**
 * SeverityBadge component for displaying severity levels
 * Supports error, warning, info, and success severity levels
 */

import { AlertCircle, AlertTriangle, Info, CheckCircle } from 'lucide-react';

type Severity = 'error' | 'warning' | 'info' | 'success';

interface SeverityBadgeProps {
  severity: Severity;
  label?: string;
  count?: number;
  size?: 'sm' | 'md' | 'lg';
}

const severityConfig: Record<
  Severity,
  {
    bg: string;
    text: string;
    icon: React.ReactNode;
  }
> = {
  error: {
    bg: 'bg-red-100 dark:bg-red-900',
    text: 'text-red-700 dark:text-red-200',
    icon: <AlertCircle size={16} />,
  },
  warning: {
    bg: 'bg-yellow-100 dark:bg-yellow-900',
    text: 'text-yellow-700 dark:text-yellow-200',
    icon: <AlertTriangle size={16} />,
  },
  info: {
    bg: 'bg-blue-100 dark:bg-blue-900',
    text: 'text-blue-700 dark:text-blue-200',
    icon: <Info size={16} />,
  },
  success: {
    bg: 'bg-green-100 dark:bg-green-900',
    text: 'text-green-700 dark:text-green-200',
    icon: <CheckCircle size={16} />,
  },
};

export function SeverityBadge({
  severity,
  label,
  count,
  size = 'md',
}: SeverityBadgeProps) {
  const config = severityConfig[severity];
  const sizeClass =
    size === 'sm'
      ? 'px-2 py-1 text-xs'
      : size === 'lg'
        ? 'px-4 py-2 text-base'
        : 'px-3 py-1.5 text-sm';

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full font-semibold ${config.bg} ${config.text} ${sizeClass}`}
    >
      {config.icon}
      <span>
        {label || severity.charAt(0).toUpperCase() + severity.slice(1)}
      </span>
      {count !== undefined && <span className="font-bold">{count}</span>}
    </div>
  );
}
