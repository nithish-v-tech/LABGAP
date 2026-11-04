import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { ScheduleItem, Experiment, StudentBatch, Laboratory } from '../types';
import { useAuth } from '../context/AuthContext';
import { CalendarCheck, Play, Trash2, Clock, Users, Building, AlertOctagon, CheckCircle2 } from 'lucide-react';
import { Badge } from '../components/Badge';

export const ScheduleOptimization: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [batches, setBatches] = useState<StudentBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [planning, setPlanning] = useState(false);

  // Planner inputs
  const [selectedExpId, setSelectedExpId] = useState<number>(1);
  const [selectedBatchId, setSelectedBatchId] = useState<number>(1);
  const [planResult, setPlanResult] = useState<any>(null);

  const fetchData = async () => {
    try {
      const [sRes, eRes, bRes] = await Promise.all([
        api.get('/schedule'),
        api.get('/experiments'),
        api.get('/batches')
      ]);
      setSchedules(sRes.data);
      setExperiments(eRes.data);
      setBatches(bRes.data);
      if (eRes.data.length > 0) setSelectedExpId(eRes.data[0].id);
      if (bRes.data.length > 0) setSelectedBatchId(bRes.data[0].id);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleGeneratePlan = async () => {
    setPlanning(true);
    setPlanResult(null);
    try {
      const res = await api.post('/schedule/optimize', {
        experiment_id: Number(selectedExpId),
        batch_id: Number(selectedBatchId),
      });
      setPlanResult(res.data);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Schedule generation failed');
    } finally {
      setPlanning(false);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Clear all scheduled rotation sessions?')) return;
    try {
      await api.delete('/schedule/clear');
      setPlanResult(null);
      fetchData();
    } catch (err) {
      alert('Failed to clear schedules');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 to-navy-900 border border-slate-800 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white tracking-wide">
              Resource-Constrained Rotation Planner
            </h2>
            <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 text-[10px] font-mono uppercase">
              Zero-Conflict Logic
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Automates student practical session allocations respecting functional equipment, safe capacity limits, and operating hours.
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={handleClearAll}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-rose-950/60 hover:text-rose-400 text-slate-300 border border-slate-700 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Reset Schedule Calendar</span>
          </button>
        )}
      </div>

      {/* Generator Tool Bar */}
      {isAdmin && (
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
          <h3 className="text-sm font-semibold text-white">Generate Feasible Student Rotation Plan</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Target Experiment</label>
              <select
                value={selectedExpId}
                onChange={(e) => setSelectedExpId(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                {experiments.map((e) => (
                  <option key={e.id} value={e.id}>{e.experiment_code} - {e.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Target Student Cohort</label>
              <select
                value={selectedBatchId}
                onChange={(e) => setSelectedBatchId(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                {batches.map((b) => (
                  <option key={b.id} value={b.id}>{b.batch_code} ({b.number_of_students} students)</option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={handleGeneratePlan}
                disabled={planning}
                className="w-full py-2.5 px-4 bg-gradient-to-r from-cyan-500 to-electric-600 hover:from-cyan-400 hover:to-electric-500 text-navy-950 font-bold rounded-xl text-xs transition-all shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2"
              >
                <Play className={`w-3.5 h-3.5 fill-current ${planning ? 'animate-spin' : ''}`} />
                <span>{planning ? 'Optimizing Constraints...' : 'Generate Rotation Schedule'}</span>
              </button>
            </div>
          </div>

          {/* Result Alert */}
          {planResult && (
            <div
              className={`p-4 rounded-xl border text-xs leading-relaxed ${
                planResult.success
                  ? 'bg-emerald-950/40 border-emerald-600/50 text-emerald-200'
                  : 'bg-rose-950/40 border-rose-600/50 text-rose-200'
              }`}
            >
              <div className="flex items-start gap-2.5">
                {planResult.success ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertOctagon className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                )}
                <div>
                  <p className="font-semibold">{planResult.message}</p>
                  {planResult.bottleneck && (
                    <p className="mt-1 text-[11px] opacity-90">
                      Constraint Bottleneck: <strong className="underline">{planResult.bottleneck}</strong> (Shortage: {planResult.equipment_shortage} units required).
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Scheduled Sessions Grid */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">
            Allocated Laboratory Rotation Sessions ({schedules.length})
          </h3>
          <span className="text-xs text-slate-400">Strictly Enforcing Safe Capacity & No Overlaps</span>
        </div>

        {schedules.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {schedules.map((s) => (
              <div
                key={s.id}
                className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-slate-700 transition-all space-y-3"
              >
                <div className="flex items-start justify-between">
                  <span className="font-mono text-xs text-cyan-400 font-bold px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800/60">
                    Session #{s.session_number}
                  </span>
                  <Badge label={s.status} />
                </div>

                <div>
                  <h4 className="text-sm font-bold text-white line-clamp-1">{s.experiment_name}</h4>
                  <p className="text-[11px] text-cyan-300 font-mono mt-0.5">{s.experiment_code} • {s.batch_code}</p>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80 space-y-1.5 text-xs text-slate-300">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" /> Date & Time:
                    </span>
                    <span className="font-mono text-white">{s.date} ({s.start_time}-{s.end_time})</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 flex items-center gap-1">
                      <Building className="w-3.5 h-3.5" /> Lab:
                    </span>
                    <span className="truncate max-w-[150px]">{s.laboratory_name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 flex items-center gap-1">
                      <Users className="w-3.5 h-3.5" /> Expected Attendance:
                    </span>
                    <span className="font-bold text-emerald-400">{s.expected_students} Students</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Post-Session Learning Gap:</span>
                    <span className="font-mono text-amber-400">{s.remaining_learning_gap} left</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-slate-500 text-xs italic">
            No rotation schedules created yet. Use the optimization engine above to generate feasible session dates.
          </div>
        )}
      </div>
    </div>
  );
};
