import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Experiment, StudentBatch } from '../types';
import { useAuth } from '../context/AuthContext';
import {
  Sparkles,
  Building2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Users,
  Wrench,
  ArrowRight,
  ShieldCheck,
  CalendarCheck
} from 'lucide-react';
import { Badge } from '../components/Badge';

export const SmartLabAllocation: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [batches, setBatches] = useState<StudentBatch[]>([]);
  const [selectedExpId, setSelectedExpId] = useState<number>(0);
  const [selectedBatchId, setSelectedBatchId] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [approving, setApproving] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState<any>(null);
  const [approvalSuccess, setApprovalSuccess] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [eRes, bRes] = await Promise.all([
          api.get('/experiments'),
          api.get('/batches')
        ]);
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
    fetchData();
  }, []);

  const handleFindBestLab = async () => {
    if (!selectedExpId || !selectedBatchId) return;
    setEvaluating(true);
    setErrorMsg(null);
    setApprovalSuccess(null);
    try {
      const res = await api.get('/schedule/smart-recommendations', {
        params: {
          experiment_id: selectedExpId,
          batch_id: selectedBatchId
        }
      });
      setEvaluationResult(res.data);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to evaluate laboratories');
    } finally {
      setEvaluating(false);
    }
  };

  const handleApproveAllocation = async (laboratoryId: number) => {
    if (!isAdmin) {
      alert('Only administrators can approve laboratory allocations.');
      return;
    }
    setApproving(true);
    setErrorMsg(null);
    try {
      const res = await api.post('/schedule/approve-allocation', {
        experiment_id: Number(selectedExpId),
        batch_id: Number(selectedBatchId),
        laboratory_id: Number(laboratoryId)
      });
      setApprovalSuccess(res.data);
      // Refresh recommendations to reflect updated bookings
      handleFindBestLab();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to approve laboratory allocation');
    } finally {
      setApproving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-cyan-400">
        <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mr-3" />
        <span>Loading Smart Allocation Engine...</span>
      </div>
    );
  }

  const best = evaluationResult?.best_recommendation;
  const alternatives = evaluationResult?.alternative_options || [];
  const rejected = evaluationResult?.rejected_laboratories || [];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-navy-900 to-blue-950 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            <h2 className="text-xl font-bold text-white tracking-wide">
              Smart Laboratory Allocation Engine
            </h2>
            <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 text-[10px] font-mono uppercase">
              Rule-Based Optimizer
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Automatically scores candidate facilities against mandatory equipment health, safe station capacity, batch headcount, and timetable contention to determine optimal laboratory placements.
          </p>
        </div>
      </div>

      {/* Selector Control Panel */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Target Curriculum & Cohort Selection
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">
              Target Student Cohort
            </label>
            <select
              value={selectedBatchId}
              onChange={(e) => setSelectedBatchId(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
            >
              {batches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.batch_code} ({b.number_of_students} Students) — {b.batch_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">
              Target Experiment / Practical Competency
            </label>
            <select
              value={selectedExpId}
              onChange={(e) => setSelectedExpId(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
            >
              {experiments.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.experiment_code} — {e.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleFindBestLab}
              disabled={evaluating}
              className="w-full py-2.5 px-4 bg-gradient-to-r from-cyan-500 to-electric-600 hover:from-cyan-400 hover:to-electric-500 text-navy-950 font-bold rounded-xl text-xs transition-all shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2"
            >
              <Sparkles className={`w-4 h-4 fill-current ${evaluating ? 'animate-spin' : ''}`} />
              <span>{evaluating ? 'Analyzing Constraints...' : 'Find Best Laboratory'}</span>
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-600/50 text-rose-300 text-xs flex items-center gap-2">
            <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {approvalSuccess && (
          <div className="p-4 rounded-xl bg-emerald-950/50 border border-emerald-600/50 text-emerald-200 text-xs space-y-1">
            <div className="flex items-center gap-2 font-bold text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
              <span>{approvalSuccess.message}</span>
            </div>
            <p className="text-[11px] text-emerald-300/80">
              Suitability Score: <strong>{approvalSuccess.suitability_score}/100</strong> • 
              <strong> {approvalSuccess.sessions_scheduled}</strong> rotation session(s) written to calendar with zero schedule collisions.
            </p>
          </div>
        )}
      </div>

      {/* Results View */}
      {evaluationResult && (
        <div className="space-y-6">
          {/* Best Recommendation Hero Card */}
          {best ? (
            <div className="p-6 rounded-2xl bg-gradient-to-br from-emerald-950/40 via-slate-900 to-navy-950 border-2 border-emerald-500/50 shadow-2xl space-y-5">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-emerald-500/20 pb-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-500 text-navy-950 text-[10px] font-black uppercase tracking-wider">
                      Rank #1 — Recommended Facility
                    </span>
                    <Badge label="Feasible & Ready" />
                  </div>
                  <h3 className="text-xl font-bold text-white tracking-wide">
                    {best.laboratory_name} ({best.laboratory_code})
                  </h3>
                  <p className="text-xs text-slate-400">
                    Location: <strong className="text-slate-300">{best.location}</strong> • Operating Hours: <strong className="text-cyan-400 font-mono">{best.operating_hours}</strong>
                  </p>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-[10px] uppercase font-bold text-slate-400">Suitability Score</p>
                    <p className="text-3xl font-black text-emerald-400 font-mono">
                      {best.suitability_score}<span className="text-xs text-slate-500">/100</span>
                    </p>
                  </div>
                  {isAdmin && (
                    <button
                      onClick={() => handleApproveAllocation(best.laboratory_id)}
                      disabled={approving}
                      className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-navy-950 font-bold text-xs shadow-lg shadow-emerald-500/20 flex items-center gap-2 transition-all"
                    >
                      <ShieldCheck className="w-4 h-4" />
                      <span>{approving ? 'Allocating...' : 'Approve Allocation'}</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Metric Highlights */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <p className="text-[10px] text-slate-400 flex items-center gap-1">
                    <Users className="w-3 h-3 text-cyan-400" /> Safe Practical Cap
                  </p>
                  <p className="text-base font-bold text-white mt-0.5">
                    {best.safe_practical_capacity} Students / Session
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Batch Headcount: {best.batch_size}</p>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <p className="text-[10px] text-slate-400 flex items-center gap-1">
                    <Wrench className="w-3 h-3 text-amber-400" /> Active Workstations
                  </p>
                  <p className="text-base font-bold text-white mt-0.5 font-mono">
                    {best.active_stations} Stations
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Shortage: {best.equipment_shortage_units} units</p>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <p className="text-[10px] text-slate-400 flex items-center gap-1">
                    <Building2 className="w-3 h-3 text-blue-400" /> Room Capacity
                  </p>
                  <p className="text-base font-bold text-white mt-0.5 font-mono">
                    {best.laboratory_capacity} Max Limit
                  </p>
                  <p className="text-[10px] text-emerald-400 mt-0.5">Compliant</p>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <p className="text-[10px] text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3 text-purple-400" /> Contention
                  </p>
                  <p className="text-base font-bold text-white mt-0.5 font-mono">
                    {best.existing_bookings_count} Bookings
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Zero collision danger</p>
                </div>
              </div>

              {/* Explainable Reasoning */}
              <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
                <p className="text-xs font-bold text-slate-300">Algorithmic Recommendation Rationale:</p>
                <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
                  {best.positive_factors.map((f: string, i: number) => (
                    <li key={i} className="text-slate-300">{f}</li>
                  ))}
                </ul>
              </div>

              {/* Equipment Inventory Health Breakdown */}
              <div className="space-y-2">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Mandatory Equipment Availability in Facility
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                  {best.equipment_breakdown.map((eq: any, idx: number) => (
                    <div key={idx} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                      <div>
                        <p className="text-xs font-semibold text-white">{eq.equipment_name}</p>
                        <p className="text-[10px] text-slate-500">Required: {eq.required_per_station} / station</p>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-mono font-bold text-emerald-400">
                          {eq.functional_available} Functional
                        </span>
                        {eq.damaged > 0 && (
                          <p className="text-[10px] text-rose-400">({eq.damaged} damaged)</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 rounded-2xl bg-rose-950/30 border border-rose-800/60 text-center space-y-2">
              <AlertTriangle className="w-8 h-8 text-rose-400 mx-auto" />
              <h3 className="text-base font-bold text-white">No Feasible Laboratory Found</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                None of the department laboratories currently possess the required functional equipment or capacity to deliver this practical safely.
              </p>
            </div>
          )}

          {/* Alternative Viable Laboratories */}
          {alternatives.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Alternative Compatible Laboratories ({alternatives.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {alternatives.map((alt: any) => (
                  <div key={alt.laboratory_id} className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          Rank #{alt.rank}
                        </span>
                        <h4 className="text-base font-bold text-white mt-1">{alt.laboratory_name}</h4>
                        <p className="text-xs text-slate-400">{alt.location}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-slate-400">Score</p>
                        <p className="text-xl font-bold font-mono text-cyan-400">{alt.suitability_score}/100</p>
                      </div>
                    </div>

                    <div className="text-xs text-slate-400 space-y-1">
                      <p>• Practical Capacity: <strong className="text-white">{alt.safe_practical_capacity}</strong></p>
                      <p>• Active Stations: <strong className="text-white">{alt.active_stations}</strong></p>
                      <p>• Existing Bookings: <strong className="text-white">{alt.existing_bookings_count}</strong></p>
                    </div>

                    {isAdmin && (
                      <button
                        onClick={() => handleApproveAllocation(alt.laboratory_id)}
                        disabled={approving}
                        className="w-full py-2 rounded-xl bg-slate-800 hover:bg-cyan-950 hover:text-cyan-400 border border-slate-700 text-xs font-semibold text-slate-200 transition-colors"
                      >
                        Approve Alternative Allocation
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Ineligible / Rejected Laboratories */}
          {rejected.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-rose-400">
                Ineligible Laboratories ({rejected.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {rejected.map((rej: any) => (
                  <div key={rej.laboratory_id} className="p-4 rounded-xl bg-slate-950/60 border border-rose-950/60 space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-bold text-slate-300">{rej.laboratory_name}</h4>
                      <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800/60 text-[10px] font-mono">
                        Score: 0 — Infeasible
                      </span>
                    </div>
                    <div className="space-y-1">
                      <p className="text-[11px] font-semibold text-rose-400">Disqualification Reasons:</p>
                      <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
                        {rej.rejection_reasons.map((r: string, idx: number) => (
                          <li key={idx} className="text-slate-400">{r}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
