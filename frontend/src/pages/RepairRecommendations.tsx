import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { RepairRecommendation } from '../types';
import { useAuth } from '../context/AuthContext';
import { Badge } from '../components/Badge';
import { Modal } from '../components/Modal';
import {
  AlertTriangle, Wrench, CheckCircle2, ArrowRight, ShieldCheck,
  Zap, Clock, Users, FlaskConical, RotateCcw
} from 'lucide-react';

export const RepairRecommendations: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [recommendations, setRecommendations] = useState<RepairRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<RepairRecommendation | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [unitsToRestore, setUnitsToRestore] = useState<number>(1);
  const [confirming, setConfirming] = useState(false);

  const fetchRepairs = async () => {
    try {
      const res = await api.get('/repairs/recommendations');
      setRecommendations(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRepairs();
  }, []);

  const handleOpenConfirm = (item: RepairRecommendation) => {
    setSelectedItem(item);
    setUnitsToRestore(item.damaged_quantity > 0 ? item.damaged_quantity : item.repairable_units);
    setIsModalOpen(true);
  };

  const handleConfirmRepair = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItem) return;
    setConfirming(true);
    try {
      await api.post('/repairs/confirm-repair', {
        equipment_id: selectedItem.equipment_id,
        action: 'mark_repaired',
        units_to_restore: Number(unitsToRestore),
        notes: 'Physical repair completed, instrument recalibrated to IEEE bench standards.',
      });
      setIsModalOpen(false);
      fetchRepairs();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to confirm repair');
    } finally {
      setConfirming(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 to-navy-900 border border-slate-800 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white tracking-wide">
              Equipment Repair Impact & Prioritization Engine
            </h2>
            <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 text-[10px] font-mono uppercase">
              ROI Optimization
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Ranks maintenance actions to unlock maximum student learning coverage without unnecessary new capital expenditure.
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-amber-400 font-mono">
          <AlertTriangle className="w-4 h-4" />
          <span>{recommendations.length} Candidate Equipment Queued</span>
        </div>
      </div>

      {/* Recommendations Cards List */}
      <div className="space-y-4">
        {recommendations.map((rec) => {
          const priorityColor =
            rec.priority === 'Critical'
              ? 'border-rose-600/60 bg-rose-950/20'
              : rec.priority === 'High'
              ? 'border-amber-600/60 bg-amber-950/20'
              : rec.priority === 'Medium'
              ? 'border-blue-600/60 bg-blue-950/20'
              : 'border-slate-700 bg-slate-900/60';

          return (
            <div
              key={rec.equipment_id}
              className={`p-5 rounded-2xl border ${priorityColor} backdrop-blur-md shadow-xl space-y-4 transition-all`}
            >
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-black/40 text-cyan-400 border border-slate-700">
                      {rec.equipment_code}
                    </span>
                    <Badge label={`${rec.priority} Priority`} />
                    <span className="text-xs text-slate-400 font-medium">• {rec.laboratory_name}</span>
                  </div>
                  <h3 className="text-base font-bold text-white">{rec.equipment_name}</h3>
                  <p className="text-xs text-slate-300 font-medium">Condition: {rec.current_condition}</p>
                </div>

                {isAdmin && (
                  <button
                    onClick={() => handleOpenConfirm(rec)}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-navy-950 transition-colors shadow-lg shadow-cyan-500/20 self-start md:self-auto"
                  >
                    <Wrench className="w-3.5 h-3.5" />
                    <span>Confirm Repair & Restore</span>
                  </button>
                )}
              </div>

              {/* Impact Metrics Row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800 text-xs">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <p className="text-[10px] uppercase text-slate-500 font-semibold">Blocked / Restricted</p>
                  <p className="font-bold text-rose-400 mt-0.5">{rec.affected_experiments_count} Experiments</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <p className="text-[10px] uppercase text-slate-500 font-semibold">Students Impacted</p>
                  <p className="font-bold text-amber-400 mt-0.5">{rec.affected_students_count} Students</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <p className="text-[10px] uppercase text-slate-500 font-semibold">Repairable Units</p>
                  <p className="font-bold text-white mt-0.5">{rec.repairable_units} Units</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <p className="text-[10px] uppercase text-slate-500 font-semibold">Capacity Gain</p>
                  <p className="font-bold text-emerald-400 mt-0.5">+{rec.potential_capacity_gain} Student Seats</p>
                </div>
              </div>

              {/* Rationale & Action Plan */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                  <span className="font-semibold text-cyan-400 flex items-center gap-1">
                    <Zap className="w-3.5 h-3.5" /> Reason for Priority Level:
                  </span>
                  <p className="text-slate-300 leading-relaxed text-[11px]">{rec.reason_for_priority}</p>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                  <span className="font-semibold text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Expected Practical Coverage Improvement:
                  </span>
                  <p className="text-slate-300 leading-relaxed text-[11px]">{rec.expected_coverage_improvement}</p>
                  <p className="text-slate-500 text-[10px] mt-1 italic">
                    Recommended Action: {rec.suggested_action}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Confirm Repair Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={`Confirm Physical Repair: ${selectedItem?.equipment_name}`}
      >
        <form onSubmit={handleConfirmRepair} className="space-y-4">
          <p className="text-xs text-slate-300">
            Rule enforcement: Equipment is never automatically marked functional. Administrator must confirm physical technician repair, safety calibration, and restored unit count.
          </p>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 text-xs">
            <div className="flex justify-between text-slate-400">
              <span>Current Damaged:</span>
              <span className="text-rose-400 font-mono font-bold">{selectedItem?.damaged_quantity} units</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>In Maintenance:</span>
              <span className="text-amber-400 font-mono font-bold">{selectedItem?.under_maintenance_quantity} units</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Already Functional:</span>
              <span className="text-emerald-400 font-mono font-bold">{selectedItem?.functional_quantity} units</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Number of Units Restored to Functional Active Status
            </label>
            <input
              type="number"
              value={unitsToRestore}
              onChange={(e) => setUnitsToRestore(Number(e.target.value))}
              min="1"
              max={selectedItem?.repairable_units || 1}
              required
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white font-mono"
            />
          </div>

          <div className="pt-3 flex justify-end gap-2 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={confirming}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-navy-950"
            >
              {confirming ? 'Updating Inventory...' : 'Confirm Restored to Functional'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
