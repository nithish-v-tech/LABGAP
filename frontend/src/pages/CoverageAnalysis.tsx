import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { CoverageAnalysisResult } from '../types';
import { Badge } from '../components/Badge';
import {
  Cpu, RotateCw, Search, Filter, AlertTriangle, CheckCircle2,
  AlertOctagon, Info, ArrowDownUp, ShieldAlert, Sparkles
} from 'lucide-react';

export const CoverageAnalysis: React.FC = () => {
  const [results, setResults] = useState<CoverageAnalysisResult[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [search, setSearch] = useState('');
  const [filterClass, setFilterClass] = useState<string>('ALL');
  const [selectedResult, setSelectedResult] = useState<CoverageAnalysisResult | null>(null);

  const runAnalysis = async () => {
    setAnalyzing(true);
    try {
      const res = await api.post('/analysis/run');
      setResults(res.data.details);
      setSummary(res.data.summary);
      if (res.data.details.length > 0 && !selectedResult) {
        setSelectedResult(res.data.details[0]);
      }
    } catch (err) {
      console.error('Failed to run coverage analysis', err);
    } finally {
      setAnalyzing(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    runAnalysis();
  }, []);

  const filtered = results.filter((r) => {
    const matchesSearch =
      r.experiment_name.toLowerCase().includes(search.toLowerCase()) ||
      r.experiment_code.toLowerCase().includes(search.toLowerCase()) ||
      r.laboratory_name.toLowerCase().includes(search.toLowerCase());

    const matchesClass = filterClass === 'ALL' || r.classification === filterClass;
    return matchesSearch && matchesClass;
  });

  return (
    <div className="space-y-6">
      {/* Header & Analyze Trigger */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 to-navy-900 border border-slate-800 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white tracking-wide">
              Deterministic Coverage & Capacity Engine
            </h2>
            <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 text-[10px] font-mono uppercase">
              Rule-Based
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Calculates actual practical delivery feasibility based on working equipment, session capacities, and laboratory operating hours.
          </p>
        </div>
        <button
          onClick={runAnalysis}
          disabled={analyzing}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-cyan-500 to-electric-600 hover:from-cyan-400 hover:to-electric-500 text-navy-950 transition-all shadow-lg shadow-cyan-500/20 active:scale-95 flex-shrink-0"
        >
          <RotateCw className={`w-4 h-4 ${analyzing ? 'animate-spin' : ''}`} />
          <span>{analyzing ? 'Evaluating Resources...' : 'Run Real-Time Analysis'}</span>
        </button>
      </div>

      {/* Summary Scoreboard */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
            <p className="text-[10px] uppercase text-emerald-400 font-semibold">Fully Covered</p>
            <p className="text-2xl font-bold text-white mt-1">{summary.fully_covered}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">100% Student Capacity</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
            <p className="text-[10px] uppercase text-amber-400 font-semibold">Partially Covered</p>
            <p className="text-2xl font-bold text-white mt-1">{summary.partially_covered}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Capacity / Time Deficit</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
            <p className="text-[10px] uppercase text-rose-400 font-semibold">Not Covered</p>
            <p className="text-2xl font-bold text-white mt-1">{summary.not_covered}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Critical Broken Equipment</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
            <p className="text-[10px] uppercase text-cyan-400 font-semibold">Total Learning Gap</p>
            <p className="text-2xl font-bold text-white mt-1">{summary.total_learning_gap}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Students Without Verified Completion</p>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-4 rounded-xl bg-slate-900/80 border border-slate-800">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search experiment code, practical name, or laboratory..."
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>
        <div>
          <select
            value={filterClass}
            onChange={(e) => setFilterClass(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Coverage Classifications</option>
            <option value="FULLY COVERED">Fully Covered</option>
            <option value="PARTIALLY COVERED">Partially Covered</option>
            <option value="NOT COVERED">Not Covered</option>
          </select>
        </div>
      </div>

      {/* Main Analysis Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Table of Evaluated Experiments */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-3">
          <h3 className="text-sm font-semibold text-white">Evaluation Results ({filtered.length} Practicals)</h3>
          <div className="overflow-x-auto max-h-[560px] overflow-y-auto pr-1">
            <table className="w-full text-left text-xs">
              <thead className="sticky top-0 bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800 z-10">
                <tr>
                  <th className="px-3 py-2.5">Experiment & Lab</th>
                  <th className="px-3 py-2.5">Status</th>
                  <th className="px-3 py-2.5 text-center">Active Stations</th>
                  <th className="px-3 py-2.5 text-center">Verified / Gap</th>
                  <th className="px-3 py-2.5 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filtered.map((item) => {
                  const isSelected = selectedResult?.experiment_id === item.experiment_id;
                  return (
                    <tr
                      key={`${item.experiment_id}-${item.batch_id}`}
                      onClick={() => setSelectedResult(item)}
                      className={`cursor-pointer transition-colors ${
                        isSelected ? 'bg-cyan-950/40 text-white' : 'hover:bg-slate-800/40 text-slate-300'
                      }`}
                    >
                      <td className="px-3 py-2.5">
                        <p className="font-semibold text-white truncate max-w-xs">{item.experiment_name}</p>
                        <p className="text-[10px] text-cyan-400 font-mono">
                          {item.experiment_code} • {item.laboratory_name}
                        </p>
                      </td>
                      <td className="px-3 py-2.5">
                        <Badge label={item.classification} />
                      </td>
                      <td className="px-3 py-2.5 text-center font-mono font-bold text-white">
                        {item.active_stations} stations
                      </td>
                      <td className="px-3 py-2.5 text-center font-mono">
                        <span className="text-emerald-400 font-bold">{item.verified_completions}</span>
                        <span className="text-slate-500"> / </span>
                        <span className="text-rose-400 font-bold">{item.remaining_learning_gap} gap</span>
                      </td>
                      <td className="px-3 py-2.5 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedResult(item);
                          }}
                          className="px-2 py-1 rounded bg-slate-800 text-cyan-400 hover:bg-slate-700 text-[10px] font-medium"
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Detailed Explainable Algorithmic Breakdown */}
        <div className="p-5 rounded-2xl bg-slate-900/95 border border-slate-800 shadow-xl space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Info className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">Algorithmic Decision Breakdown</h3>
          </div>

          {selectedResult ? (
            <div className="space-y-4 text-xs">
              <div>
                <p className="text-[10px] uppercase font-mono text-cyan-400">{selectedResult.experiment_code}</p>
                <h4 className="text-sm font-bold text-white mt-0.5">{selectedResult.experiment_name}</h4>
                <p className="text-slate-400 text-[11px] mt-0.5">{selectedResult.laboratory_name}</p>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Coverage Classification:</span>
                  <Badge label={selectedResult.classification} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Bottleneck Equipment:</span>
                  <span className="font-semibold text-rose-400">{selectedResult.bottleneck_equipment || 'None'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Equipment Shortage:</span>
                  <span className="font-mono font-bold text-white">
                    {selectedResult.equipment_shortage > 0 ? `-${selectedResult.equipment_shortage} units` : '0 units'}
                  </span>
                </div>
              </div>

              {/* Mathematical Capacity Calculation */}
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 font-mono text-[11px]">
                <p className="text-cyan-400 font-bold uppercase tracking-wider text-[10px]">Mathematical Capacity Proof</p>
                <div className="space-y-1 text-slate-300">
                  <p>• Active Stations = {selectedResult.active_stations}</p>
                  <p>• Capacity / Session = {selectedResult.safe_capacity_per_session} students</p>
                  <p>• Assigned Cohort Size = {selectedResult.batch_size} students</p>
                  <p>• Total Available Slots = {selectedResult.available_capacity} seats</p>
                  <p>• Remaining Unverified Gap = {selectedResult.remaining_learning_gap} students ({selectedResult.gap_percentage}%)</p>
                </div>
              </div>

              {/* Explainable Text Rationale */}
              <div className="p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-800/40 text-slate-300 leading-relaxed space-y-1">
                <p className="font-semibold text-cyan-400 text-[11px]">Explanation Behind Result:</p>
                <p className="text-[11px]">{selectedResult.reason}</p>
              </div>
            </div>
          ) : (
            <p className="text-slate-500 text-xs italic">Select an experiment to view explainable mathematical breakdown.</p>
          )}
        </div>
      </div>
    </div>
  );
};
