import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Experiment, Laboratory, Equipment } from '../types';
import { useAuth } from '../context/AuthContext';
import { Modal } from '../components/Modal';
import { Badge } from '../components/Badge';
import {
  FlaskConical, Plus, Search, Filter, Clock, Users,
  Wrench, CheckCircle, AlertTriangle, AlertOctagon, Trash2, Edit
} from 'lucide-react';

export const Experiments: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [labs, setLabs] = useState<Laboratory[]>([]);
  const [allEquipment, setAllEquipment] = useState<Equipment[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedLab, setSelectedLab] = useState<string>('ALL');
  const [selectedCoverage, setSelectedCoverage] = useState<string>('ALL');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingExp, setEditingExp] = useState<Experiment | null>(null);

  // Form
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [labId, setLabId] = useState<number>(1);
  const [competency, setCompetency] = useState('');
  const [duration, setDuration] = useState(2.0);
  const [studentsPerUnit, setStudentsPerUnit] = useState(2);
  const [minBatch, setMinBatch] = useState(4);
  const [maxBatch, setMaxBatch] = useState(24);
  const [criteria, setCriteria] = useState('');
  const [selectedEquipmentId, setSelectedEquipmentId] = useState<number>(1);

  const fetchData = async () => {
    try {
      const [expRes, labRes, eqRes] = await Promise.all([
        api.get('/experiments'),
        api.get('/laboratories'),
        api.get('/equipment')
      ]);
      setExperiments(expRes.data);
      setLabs(labRes.data);
      setAllEquipment(eqRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenAdd = () => {
    setEditingExp(null);
    setCode(`EXP-DEMO-${experiments.length + 1}`);
    setName('');
    setLabId(labs[0]?.id || 1);
    setCompetency('');
    setDuration(2.0);
    setStudentsPerUnit(2);
    setMinBatch(4);
    setMaxBatch(24);
    setCriteria('Practical circuit demonstration, calibrated reading verification and faculty viva.');
    setSelectedEquipmentId(allEquipment[0]?.id || 1);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (exp: Experiment) => {
    setEditingExp(exp);
    setCode(exp.experiment_code);
    setName(exp.name);
    setLabId(exp.laboratory_id);
    setCompetency(exp.practical_competency);
    setDuration(exp.duration_hours);
    setStudentsPerUnit(exp.students_per_unit);
    setMinBatch(exp.min_safe_batch_size);
    setMaxBatch(exp.max_safe_batch_size);
    setCriteria(exp.completion_criteria);
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this practical experiment?')) return;
    try {
      await api.delete(`/experiments/${id}`);
      fetchData();
    } catch (err) {
      alert('Failed to delete experiment');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingExp) {
        await api.put(`/experiments/${editingExp.id}`, {
          name,
          laboratory_id: Number(labId),
          practical_competency: competency,
          duration_hours: Number(duration),
          students_per_unit: Number(studentsPerUnit),
          min_safe_batch_size: Number(minBatch),
          max_safe_batch_size: Number(maxBatch),
          completion_criteria: criteria,
        });
      } else {
        await api.post('/experiments', {
          experiment_code: code,
          name,
          laboratory_id: Number(labId),
          practical_competency: competency,
          duration_hours: Number(duration),
          students_per_unit: Number(studentsPerUnit),
          min_safe_batch_size: Number(minBatch),
          max_safe_batch_size: Number(maxBatch),
          completion_criteria: criteria,
          equipment_requirements: [
            { equipment_id: Number(selectedEquipmentId), quantity_required: 1, is_critical: true }
          ]
        });
      }
      setIsModalOpen(false);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to save experiment');
    }
  };

  // Filter experiments
  const filtered = experiments.filter((e) => {
    const matchesSearch =
      e.name.toLowerCase().includes(search.toLowerCase()) ||
      e.experiment_code.toLowerCase().includes(search.toLowerCase()) ||
      e.practical_competency.toLowerCase().includes(search.toLowerCase());

    const matchesLab = selectedLab === 'ALL' || String(e.laboratory_id) === selectedLab;
    const matchesCoverage = selectedCoverage === 'ALL' || e.coverage_classification === selectedCoverage;

    return matchesSearch && matchesLab && matchesCoverage;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Prescribed Practical Curriculum</h2>
          <p className="text-xs text-slate-400">
            {experiments.length} accredited syllabus experiments mapped to required laboratory equipment.
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={handleOpenAdd}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-navy-950 transition-colors shadow-lg shadow-cyan-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Add Experiment</span>
          </button>
        )}
      </div>

      {/* Filters Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-4 rounded-xl bg-slate-900/80 border border-slate-800">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search experiment, code, or competency..."
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div>
          <select
            value={selectedLab}
            onChange={(e) => setSelectedLab(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Laboratories</option>
            {labs.map((l) => (
              <option key={l.id} value={String(l.id)}>{l.name}</option>
            ))}
          </select>
        </div>

        <div>
          <select
            value={selectedCoverage}
            onChange={(e) => setSelectedCoverage(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Coverage Statuses</option>
            <option value="FULLY COVERED">Fully Covered</option>
            <option value="PARTIALLY COVERED">Partially Covered</option>
            <option value="NOT COVERED">Not Covered</option>
          </select>
        </div>
      </div>

      {/* Experiment Cards / Table */}
      <div className="space-y-3">
        {filtered.map((exp) => (
          <div
            key={exp.id}
            className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all shadow-lg space-y-3"
          >
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-cyan-400 font-semibold px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800/60">
                    {exp.experiment_code}
                  </span>
                  <Badge label={exp.coverage_classification || 'NOT EVALUATED'} />
                  <span className="text-xs text-slate-400 font-medium">• {exp.laboratory_name}</span>
                </div>
                <h3 className="text-base font-bold text-white">{exp.name}</h3>
                <p className="text-xs text-cyan-300 font-medium">Competency: {exp.practical_competency}</p>
              </div>

              {isAdmin && (
                <div className="flex items-center gap-2 self-end md:self-auto">
                  <button
                    onClick={() => handleOpenEdit(exp)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-colors"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(exp.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {/* Constraints & Specs Pills */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800/80 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <p className="text-[10px] uppercase text-slate-500 font-semibold">Duration</p>
                <p className="font-semibold text-slate-200 mt-0.5">{exp.duration_hours} Hours</p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <p className="text-[10px] uppercase text-slate-500 font-semibold">Station Grouping</p>
                <p className="font-semibold text-slate-200 mt-0.5">{exp.students_per_unit} Students / Station</p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <p className="text-[10px] uppercase text-slate-500 font-semibold">Safe Session Cap</p>
                <p className="font-semibold text-slate-200 mt-0.5">{exp.safe_capacity_per_session || 0} Students</p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <p className="text-[10px] uppercase text-slate-500 font-semibold">Equipment Shortage</p>
                <p className={`font-semibold mt-0.5 ${exp.equipment_shortage ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {exp.equipment_shortage ? `-${exp.equipment_shortage} Units` : '0 Units'}
                </p>
              </div>
            </div>

            {/* Required Equipment & Reason */}
            <div className="text-xs space-y-1.5 bg-slate-950/40 p-3 rounded-xl border border-slate-800/60">
              <div className="flex items-center gap-2 text-slate-400">
                <Wrench className="w-3.5 h-3.5 text-cyan-400" />
                <span className="font-medium text-slate-300">Required Equipment:</span>
                <span className="text-slate-400">
                  {exp.equipment_requirements && exp.equipment_requirements.length > 0
                    ? exp.equipment_requirements.map((r) => `${r.equipment_name} (${r.functional_available} avail)`).join(', ')
                    : 'Standard Laboratory Workstation'}
                </span>
              </div>
              {exp.reason && (
                <p className="text-[11px] text-slate-400 pl-5 leading-relaxed">
                  <span className="text-slate-500 font-medium">Algorithmic Feasibility Rationale: </span>
                  {exp.reason}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Add / Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingExp ? 'Edit Experiment' : 'Add Practical Experiment'}
        maxWidth="xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Experiment Code</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                disabled={!!editingExp}
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Assigned Laboratory</label>
              <select
                value={labId}
                onChange={(e) => setLabId(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
              >
                {labs.map((l) => (
                  <option key={l.id} value={l.id}>{l.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Experiment Title</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
              placeholder="e.g. Inverting Op-Amp Analysis"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Practical Learning Competency</label>
            <input
              type="text"
              value={competency}
              onChange={(e) => setCompetency(e.target.value)}
              required
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
              placeholder="e.g. Analog Circuit Feedback Design"
            />
          </div>

          {!editingExp && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Primary Required Equipment</label>
              <select
                value={selectedEquipmentId}
                onChange={(e) => setSelectedEquipmentId(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
              >
                {allEquipment.map((eq) => (
                  <option key={eq.id} value={eq.id}>
                    {eq.equipment_code} - {eq.name} ({eq.functional_quantity} functional)
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="grid grid-cols-4 gap-2">
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">Duration (Hours)</label>
              <input
                type="number"
                step="0.5"
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                min="0.5"
                max="6"
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-2.5 py-2 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">Students/Unit</label>
              <input
                type="number"
                value={studentsPerUnit}
                onChange={(e) => setStudentsPerUnit(Number(e.target.value))}
                min="1"
                max="6"
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-2.5 py-2 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">Min Safe Batch</label>
              <input
                type="number"
                value={minBatch}
                onChange={(e) => setMinBatch(Number(e.target.value))}
                min="2"
                max="30"
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-2.5 py-2 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">Max Safe Batch</label>
              <input
                type="number"
                value={maxBatch}
                onChange={(e) => setMaxBatch(Number(e.target.value))}
                min="4"
                max="40"
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-2.5 py-2 text-xs text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Verification Criteria</label>
            <textarea
              value={criteria}
              onChange={(e) => setCriteria(e.target.value)}
              rows={2}
              required
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
            />
          </div>

          <div className="pt-3 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-navy-950"
            >
              Save Experiment
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
