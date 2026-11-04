import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: string;
  trendPositive?: boolean;
  color?: 'cyan' | 'blue' | 'emerald' | 'amber' | 'rose' | 'purple';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendPositive = true,
  color = 'cyan',
}) => {
  const colorMap = {
    cyan: 'text-cyan-400 bg-cyan-950/60 border-cyan-500/20 group-hover:border-cyan-500/40',
    blue: 'text-sky-400 bg-sky-950/60 border-sky-500/20 group-hover:border-sky-500/40',
    emerald: 'text-emerald-400 bg-emerald-950/60 border-emerald-500/20 group-hover:border-emerald-500/40',
    amber: 'text-amber-400 bg-amber-950/60 border-amber-500/20 group-hover:border-amber-500/40',
    rose: 'text-rose-400 bg-rose-950/60 border-rose-500/20 group-hover:border-rose-500/40',
    purple: 'text-purple-400 bg-purple-950/60 border-purple-500/20 group-hover:border-purple-500/40',
  };

  return (
    <div className="group relative bg-slate-900/80 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 hover:border-slate-700 transition-all duration-200 shadow-lg shadow-black/20">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{title}</p>
          <p className="text-2xl font-bold tracking-tight text-white">{value}</p>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
        </div>
        <div className={`p-2.5 rounded-lg border transition-colors ${colorMap[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      {trend && (
        <div className="mt-3 flex items-center gap-1.5 text-xs">
          <span className={trendPositive ? 'text-emerald-400 font-medium' : 'text-rose-400 font-medium'}>
            {trend}
          </span>
          <span className="text-slate-500">vs target capacity</span>
        </div>
      )}
    </div>
  );
};
