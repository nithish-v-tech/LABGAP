import React, { useEffect, useState } from 'react';
import { StatCard } from '../components/StatCard';
import { Badge } from '../components/Badge';
import { api } from '../services/api';
import { DashboardSummary } from '../types';
import {
  Building2, FlaskConical, Users, Wrench, AlertOctagon, CheckCircle,
  Clock, ArrowUpRight, ShieldAlert, Cpu
} from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';

interface OverviewProps {
  onNavigateTab: (tab: string) => void;
}

export const Overview: React.FC<OverviewProps> = ({ onNavigateTab }) => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [attentionList, setAttentionList] = useState<any[]>([]);

  const fetchSummary = async () => {
    try {
      const res = await api.get('/analysis/summary');
      setData(res.data);
      const expsRes = await api.get('/experiments');
      const filtered = expsRes.data.filter((e: any) => e.coverage_classification !== 'FULLY COVERED');
      setAttentionList(filtered.slice(0, 5));
    } catch (err) {
      console.error('Failed to load dashboard summary', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-cyan-400">
          <div className="w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-medium">Loading institutional laboratory analytics...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 to-navy-900 border border-slate-800 shadow-xl">
        <div className="space-y-1">
          <h2 className="text-xl font-bold text-white tracking-wide">
            Laboratory Resource & Learning Gap Command Center
          </h2>
          <p className="text-xs text-slate-400">
            Real-time equipment availability mapping, safe student capacity, and verified practical learning coverage.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigateTab('coverage')}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-navy-950 transition-colors shadow-lg shadow-cyan-500/20"
          >
            <Cpu className="w-4 h-4" />
            <span>Run Coverage Analysis</span>
          </button>
          <button
            onClick={() => onNavigateTab('repairs')}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            <Wrench className="w-4 h-4" />
            <span>Repair Recommendations</span>
          </button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Practical Experiments"
          value={data?.total_experiments || 0}
          subtitle={`${data?.fully_covered_experiments || 0} Fully Covered`}
          icon={FlaskConical}
          color="cyan"
        />
        <StatCard
          title="Equipment Inventory"
          value={data?.total_equipment_units || 0}
          subtitle={`${data?.functional_equipment || 0} Functional (${data?.equipment_utilization_rate || 0}%)`}
          icon={Wrench}
          color="blue"
        />
        <StatCard
          title="Student Learning Gap"
          value={data?.total_practical_learning_gap || 0}
          subtitle="Unverified Practical Competencies"
          icon={AlertOctagon}
          color="amber"
          trend={`${data?.total_verified_competencies || 0} verified`}
          trendPositive={false}
        />
        <StatCard
          title="Critical Bottlenecks"
          value={data?.not_covered_experiments || 0}
          subtitle="Experiments with 0 Safe Delivery"
          icon={ShieldAlert}
          color="rose"
        />
      </div>

      {/* Secondary Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <p className="text-[11px] text-slate-400 uppercase font-medium">Laboratories</p>
          <p className="text-xl font-bold text-white mt-1">{data?.total_laboratories || 0}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">Across Department</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <p className="text-[11px] text-slate-400 uppercase font-medium">Enrolled Students</p>
          <p className="text-xl font-bold text-white mt-1">{data?.total_students || 0}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">Across {data?.total_batches || 0} Batches</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <p className="text-[11px] text-slate-400 uppercase font-medium">Damaged Units</p>
          <p className="text-xl font-bold text-rose-400 mt-1">{data?.damaged_equipment || 0}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">Immediate repair candidates</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <p className="text-[11px] text-slate-400 uppercase font-medium">In Maintenance</p>
          <p className="text-xl font-bold text-amber-400 mt-1">{data?.under_maintenance || 0}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">Under technician inspection</p>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Experiment Coverage Distribution */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Curriculum Delivery Feasibility</h3>
              <p className="text-xs text-slate-400">Coverage classification based on working equipment & hours</p>
            </div>
            <button
              onClick={() => onNavigateTab('coverage')}
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium"
            >
              <span>Inspect</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
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
                <Legend
                  formatter={(value) => <span className="text-xs text-slate-300">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Equipment Condition Distribution */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Equipment Operational Health</h3>
              <p className="text-xs text-slate-400">Units across functional, partially functional, damaged, maintenance</p>
            </div>
            <button
              onClick={() => onNavigateTab('equipment')}
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium"
            >
              <span>Inventory</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
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

      {/* Attention Table */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white">Experiments Requiring Immediate Attention</h3>
            <p className="text-xs text-slate-400">Experiments blocked or restricted by equipment condition</p>
          </div>
          <button
            onClick={() => onNavigateTab('experiments')}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium"
          >
            View All Experiments →
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Experiment</th>
                <th className="px-4 py-3">Laboratory</th>
                <th className="px-4 py-3">Competency</th>
                <th className="px-4 py-3">Coverage Status</th>
                <th className="px-4 py-3">Equipment Shortage</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {attentionList.map((exp) => (
                <tr key={exp.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3">
                    <p className="font-semibold text-white">{exp.name}</p>
                    <p className="text-[10px] text-slate-400 font-mono">{exp.experiment_code}</p>
                  </td>
                  <td className="px-4 py-3 text-slate-300">{exp.laboratory_name}</td>
                  <td className="px-4 py-3 text-slate-400">{exp.practical_competency}</td>
                  <td className="px-4 py-3">
                    <Badge label={exp.coverage_classification} />
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-rose-400 font-semibold">
                      {exp.equipment_shortage > 0 ? `-${exp.equipment_shortage} units` : '0 units'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => onNavigateTab('coverage')}
                      className="text-xs text-cyan-400 hover:underline"
                    >
                      Audit →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
