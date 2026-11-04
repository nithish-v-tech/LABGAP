import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import {
  Lightbulb,
  Wrench,
  Building,
  AlertOctagon,
  TrendingUp,
  Cpu,
  Clock,
  ArrowRight,
  ShieldAlert,
  Sparkles
} from 'lucide-react';
import { Badge } from '../components/Badge';

export const ResourceIntelligence: React.FC = () => {
  const [intelligenceData, setIntelligenceData] = useState<any>(null);
  const [summaryData, setSummaryData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [intelRes, sumRes] = await Promise.all([
        api.get('/analysis/resource-intelligence'),
        api.get('/analysis/summary')
      ]);
      setIntelligenceData(intelRes.data);
      setSummaryData(sumRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-cyan-400">
        <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mr-3" />
        <span>Aggregating Institutional Resource Intelligence...</span>
      </div>
    );
  }

  const recs = intelligenceData?.recommendations || [];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-navy-900 to-indigo-950 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-amber-400" />
            <h2 className="text-xl font-bold text-white tracking-wide">
              Resource Intelligence & Decision Engine
            </h2>
            <span className="px-2 py-0.5 rounded bg-indigo-950 text-indigo-400 border border-indigo-800 text-[10px] font-mono uppercase">
              Actionable Directives
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Synthesizes current hardware inventory conditions, laboratory time utilisation, and curriculum bottlenecks into prioritized operational recommendations.
          </p>
        </div>
      </div>

      {/* Hardware & Coverage Pulse */}
      {summaryData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
            <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" /> Equipment Utilization
            </p>
            <p className="text-2xl font-bold text-cyan-400 font-mono">
              {summaryData.equipment_utilization_rate}%
            </p>
            <p className="text-[10px] text-slate-500">
              {summaryData.functional_equipment} / {summaryData.total_equipment_units} Units Functional
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
            <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
              <Wrench className="w-3.5 h-3.5 text-rose-400" /> Broken Equipment
            </p>
            <p className="text-2xl font-bold text-rose-400 font-mono">
              {summaryData.damaged_equipment + summaryData.under_maintenance}
            </p>
            <p className="text-[10px] text-slate-500">Damaged or in Maintenance</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
            <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
              <AlertOctagon className="w-3.5 h-3.5 text-amber-400" /> Curriculum Blockers
            </p>
            <p className="text-2xl font-bold text-amber-400 font-mono">
              {summaryData.not_covered_experiments} Experiments
            </p>
            <p className="text-[10px] text-rose-300">Classified NOT COVERED</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
            <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
              <Building className="w-3.5 h-3.5 text-emerald-400" /> Fully Covered
            </p>
            <p className="text-2xl font-bold text-emerald-400 font-mono">
              {summaryData.fully_covered_experiments} Experiments
            </p>
            <p className="text-[10px] text-slate-500">100% Practical Delivery Feasible</p>
          </div>
        </div>
      )}

      {/* Generated Recommendations List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            Prioritized Operational Recommendations ({recs.length})
          </h3>
          <span className="text-[11px] text-slate-400">Derived strictly from active database state</span>
        </div>

        {recs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recs.map((rec: any, idx: number) => {
              const isCrit = rec.priority === 'Critical';
              const isHigh = rec.priority === 'High';
              const isMed = rec.priority === 'Medium';

              return (
                <div
                  key={idx}
                  className={`p-5 rounded-2xl border transition-all space-y-3 ${
                    isCrit
                      ? 'bg-rose-950/20 border-rose-800/60 hover:border-rose-700'
                      : isHigh
                      ? 'bg-amber-950/20 border-amber-800/60 hover:border-amber-700'
                      : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {rec.category}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        isCrit
                          ? 'bg-rose-950 text-rose-400 border border-rose-800'
                          : isHigh
                          ? 'bg-amber-950 text-amber-400 border border-amber-800'
                          : 'bg-blue-950 text-blue-400 border border-blue-800'
                      }`}
                    >
                      {rec.priority} Priority
                    </span>
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-white">{rec.title}</h4>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                      {rec.explanation}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between">
                    <span className="text-[11px] text-cyan-400 font-semibold flex items-center gap-1">
                      Action: {rec.action}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-8 text-center text-slate-500 text-xs italic">
            No active resource bottlenecks or repair directives detected.
          </div>
        )}
      </div>
    </div>
  );
};
