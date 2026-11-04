import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { DashboardSummary, RepairRecommendation } from '../types';
import { StatCard } from '../components/StatCard';
import { Badge } from '../components/Badge';
import {
  Building2, FlaskConical, Users, Wrench, AlertTriangle,
  CheckCircle2, ArrowUpRight, ShieldCheck, FileText, Lock
} from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';

export const HodAnalytics: React.FC = () => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [repairs, setRepairs] = useState<RepairRecommendation[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHodData = async () => {
    try {
      const [sumRes, repRes] = await Promise.all([
        api.get('/analysis/summary'),
        api.get('/repairs/recommendations')
      ]);
      setData(sumRes.data);
      setRepairs(repRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHodData();
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-cyan-400 text-xs">Loading department executive analytics...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Executive Banner */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-purple-950/40 via-slate-900 to-navy-900 border border-purple-800/40 shadow-xl space-y-1">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-bold text-white tracking-wide">
            Head of Department Executive Review
          </h2>
          <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-purple-950 text-purple-300 border border-purple-700/60 text-[10px] font-semibold">
            <Lock className="w-3 h-3" /> Read-Only Oversight
          </span>
        </div>
        <p className="text-xs text-slate-400">
          Curriculum compliance audits, student competency gaps, and resource repair prioritization for department leadership.
        </p>
      </div>

      {/* High-level KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Practical Delivery Feasibility"
          value={`${data?.fully_covered_experiments || 0} / ${data?.total_experiments || 0}`}
          subtitle={`${data?.not_covered_experiments || 0} critical bottlenecks`}
          icon={FlaskConical}
          color="cyan"
        />
        <StatCard
          title="Department Learning Gap"
          value={data?.total_practical_learning_gap || 0}
          subtitle="Students lacking verified competencies"
          icon={AlertTriangle}
          color="amber"
          trend={`${data?.total_verified_competencies || 0} completions`}
          trendPositive={false}
        />
        <StatCard
          title="Functional Equipment Rate"
          value={`${data?.equipment_utilization_rate || 0}%`}
          subtitle={`${data?.functional_equipment || 0} of ${data?.total_equipment_units || 0} active`}
          icon={Wrench}
          color="emerald"
        />
        <StatCard
          title="High-Priority Repairs"
          value={repairs.filter(r => r.priority === 'Critical' || r.priority === 'High').length}
          subtitle="Equipment restoration candidates"
          icon={Building2}
          color="rose"
        />
      </div>

      {/* Analytical Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-3">
          <h3 className="text-sm font-semibold text-white">Syllabus Delivery Coverage Breakdown</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data?.coverage_distribution || []}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                >
                  {data?.coverage_distribution?.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend formatter={(value) => <span className="text-xs text-slate-300">{value}</span>} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-3">
          <h3 className="text-sm font-semibold text-white">Equipment Operational Condition</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.condition_distribution || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {data?.condition_distribution?.map((entry, index) => (
                    <Cell key={`bar-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Repair Priorities Oversight */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white">Resource Bottlenecks & Repair Priorities</h3>
            <p className="text-xs text-slate-400">Equipment ranking based on potential student capacity restoration</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Equipment</th>
                <th className="px-4 py-3">Laboratory</th>
                <th className="px-4 py-3 text-center">Damaged Units</th>
                <th className="px-4 py-3 text-center">Capacity Improvement</th>
                <th className="px-4 py-3">Action Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {repairs.slice(0, 6).map((r) => (
                <tr key={r.equipment_id} className="hover:bg-slate-800/30">
                  <td className="px-4 py-3"><Badge label={r.priority} /></td>
                  <td className="px-4 py-3 font-semibold text-white">
                    {r.equipment_name}
                    <span className="block text-[10px] text-cyan-400 font-mono">{r.equipment_code}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-300">{r.laboratory_name}</td>
                  <td className="px-4 py-3 text-center font-bold text-rose-400 font-mono">{r.damaged_quantity}</td>
                  <td className="px-4 py-3 text-center font-bold text-emerald-400 font-mono">+{r.potential_capacity_gain} seats</td>
                  <td className="px-4 py-3 text-[11px] text-slate-400 max-w-sm">{r.reason_for_priority}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
