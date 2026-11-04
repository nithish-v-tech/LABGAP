import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { StudentBatch, Experiment, Faculty } from '../types';
import { useAuth } from '../context/AuthContext';
import { Modal } from '../components/Modal';
import { Users, Plus, CheckSquare, BookOpen, GraduationCap, ArrowRight } from 'lucide-react';

export const StudentBatches: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [batches, setBatches] = useState<StudentBatch[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [facultyList, setFacultyList] = useState<Faculty[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [activeBatch, setActiveBatch] = useState<StudentBatch | null>(null);

  // Form states
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [studentCount, setStudentCount] = useState(24);
  const [assignedFacultyId, setAssignedFacultyId] = useState<number | undefined>(undefined);
  const [selectedExpIds, setSelectedExpIds] = useState<number[]>([]);

  const fetchData = async () => {
    try {
      const [bRes, expRes, facRes] = await Promise.all([
        api.get('/batches'),
        api.get('/experiments'),
        api.get('/faculty')
      ]);
      setBatches(bRes.data);
      setExperiments(expRes.data);
      setFacultyList(facRes.data);
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
    setCode(`BATCH-2026-${String.fromCharCode(65 + batches.length)}`);
    setName('');
    setStudentCount(24);
    setAssignedFacultyId(facultyList[0]?.id);
    setIsModalOpen(true);
  };

  const handleOpenAssign = (batch: StudentBatch) => {
    setActiveBatch(batch);
    const existing = batch.assigned_experiments?.map((e) => e.id) || [];
    setSelectedExpIds(existing);
    setIsAssignModalOpen(true);
  };

  const handleSubmitBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/batches', {
        department_id: 1,
        laboratory_id: 1,
        batch_code: code,
        batch_name: name,
        number_of_students: Number(studentCount),
        assigned_faculty_id: assignedFacultyId ? Number(assignedFacultyId) : null,
      });
      setIsModalOpen(false);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create batch');
    }
  };

  const handleSaveAssignments = async () => {
    if (!activeBatch) return;
    try {
      await api.post(`/batches/${activeBatch.id}/assign-experiments`, selectedExpIds);
      setIsAssignModalOpen(false);
      fetchData();
    } catch (err) {
      alert('Failed to update batch experiment assignments');
    }
  };

  const toggleExperimentSelection = (id: number) => {
    if (selectedExpIds.includes(id)) {
      setSelectedExpIds(selectedExpIds.filter((x) => x !== id));
    } else {
      setSelectedExpIds([...selectedExpIds, id]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Student Batches & Curriculum Assignments</h2>
          <p className="text-xs text-slate-400">
            Student cohort management and mapping to required laboratory curriculum practicals.
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={handleOpenAdd}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-navy-950 transition-colors shadow-lg shadow-cyan-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Create Batch</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {batches.map((batch) => (
          <div
            key={batch.id}
            className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4 flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <span className="font-mono text-xs font-semibold text-cyan-400 px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800/60">
                    {batch.batch_code}
                  </span>
                  <h3 className="text-base font-bold text-white mt-1.5">{batch.batch_name}</h3>
                </div>
                <div className="p-2 rounded-xl bg-slate-950 border border-slate-800 text-center">
                  <p className="text-xs font-bold text-cyan-400 font-mono">{batch.number_of_students}</p>
                  <p className="text-[9px] uppercase text-slate-500">Students</p>
                </div>
              </div>

              <div className="text-xs space-y-1.5 text-slate-400">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Instructor:</span>
                  <span className="text-slate-200 font-medium">{batch.assigned_faculty_name || 'Dr. Rajesh Ramanathan'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Home Laboratory:</span>
                  <span className="text-slate-200">{batch.laboratory_name || 'Block B Electronics Lab'}</span>
                </div>
              </div>

              {/* Assigned Practicals List */}
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-300">Assigned Curriculum</span>
                  <span className="text-[10px] text-cyan-400 font-mono">
                    {batch.assigned_experiments?.length || 0} Practicals
                  </span>
                </div>
                <div className="space-y-1 max-h-32 overflow-y-auto pr-1">
                  {batch.assigned_experiments && batch.assigned_experiments.length > 0 ? (
                    batch.assigned_experiments.map((e) => (
                      <div key={e.id} className="flex items-center gap-2 text-[11px] text-slate-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 flex-shrink-0" />
                        <span className="truncate">{e.name}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-[11px] text-slate-500 italic">No experiments assigned yet.</p>
                  )}
                </div>
              </div>
            </div>

            {isAdmin && (
              <button
                onClick={() => handleOpenAssign(batch)}
                className="w-full mt-2 py-2 px-3 rounded-xl text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition-colors flex items-center justify-center gap-1.5"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>Assign / Modify Curriculum</span>
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Create Batch Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create Student Batch">
        <form onSubmit={handleSubmitBatch} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Batch Code</label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Batch Title</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
              placeholder="e.g. 3rd Year EEE - Section A"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Student Count</label>
              <input
                type="number"
                value={studentCount}
                onChange={(e) => setStudentCount(Number(e.target.value))}
                min="1"
                max="60"
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Assigned Faculty</label>
              <select
                value={assignedFacultyId}
                onChange={(e) => setAssignedFacultyId(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
              >
                {facultyList.map((f) => (
                  <option key={f.id} value={f.id}>{f.name}</option>
                ))}
              </select>
            </div>
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
              Create Batch
            </button>
          </div>
        </form>
      </Modal>

      {/* Assign Experiments Modal */}
      <Modal
        isOpen={isAssignModalOpen}
        onClose={() => setIsAssignModalOpen(false)}
        title={`Assign Experiments to ${activeBatch?.batch_code}`}
        maxWidth="xl"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-400">
            Select curriculum experiments assigned to <strong className="text-white">{activeBatch?.batch_name}</strong>.
          </p>

          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {experiments.map((exp) => {
              const isChecked = selectedExpIds.includes(exp.id);
              return (
                <div
                  key={exp.id}
                  onClick={() => toggleExperimentSelection(exp.id)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                    isChecked
                      ? 'bg-cyan-950/40 border-cyan-500/50 text-white'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="space-y-0.5">
                    <p className="text-xs font-bold text-white">{exp.name}</p>
                    <p className="text-[10px] text-cyan-400 font-mono">{exp.experiment_code} • {exp.practical_competency}</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => {}}
                    className="w-4 h-4 rounded text-cyan-500 focus:ring-0 bg-slate-900 border-slate-700"
                  />
                </div>
              );
            })}
          </div>

          <div className="pt-3 flex justify-end gap-2 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsAssignModalOpen(false)}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSaveAssignments}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-navy-950"
            >
              Save Assigned Practicals ({selectedExpIds.length})
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
