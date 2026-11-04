import React from 'react';

interface BadgeProps {
  label: string;
  variant?: 'green' | 'amber' | 'red' | 'cyan' | 'blue' | 'purple' | 'gray';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ label, variant = 'cyan', size = 'sm' }) => {
  const variantStyles = {
    green: 'bg-emerald-950/80 text-emerald-400 border-emerald-500/30',
    amber: 'bg-amber-950/80 text-amber-400 border-amber-500/30',
    red: 'bg-rose-950/80 text-rose-400 border-rose-500/30',
    cyan: 'bg-cyan-950/80 text-cyan-400 border-cyan-500/30',
    blue: 'bg-blue-950/80 text-blue-400 border-blue-500/30',
    purple: 'bg-purple-950/80 text-purple-400 border-purple-500/30',
    gray: 'bg-slate-800/80 text-slate-400 border-slate-700/40',
  };

  const sizeStyles = {
    sm: 'text-xs px-2.5 py-0.5',
    md: 'text-sm px-3 py-1',
  };

  // Helper mapping if standard classifications are passed
  let resolvedVariant = variant;
  const upper = label.toUpperCase();
  if (upper.includes('FULLY COVERED') || upper.includes('VERIFIED') || upper.includes('COMPLETED') || upper.includes('NORMAL')) {
    resolvedVariant = 'green';
  } else if (upper.includes('PARTIALLY COVERED') || upper.includes('PENDING') || upper.includes('SCHEDULED') || upper.includes('MEDIUM')) {
    resolvedVariant = 'amber';
  } else if (upper.includes('NOT COVERED') || upper.includes('REJECTED') || upper.includes('CRITICAL') || upper.includes('DAMAGED')) {
    resolvedVariant = 'red';
  } else if (upper.includes('HIGH')) {
    resolvedVariant = 'amber';
  } else if (upper.includes('LOW')) {
    resolvedVariant = 'blue';
  }

  return (
    <span className={`inline-flex items-center font-medium rounded-full border ${variantStyles[resolvedVariant]} ${sizeStyles[size]}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-80" />
      {label}
    </span>
  );
};
