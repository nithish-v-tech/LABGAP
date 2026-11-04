import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Laboratory } from '../types';
import { useAuth } from '../context/AuthContext';
import { Modal } from '../components/Modal';
import { Building2, Plus, Edit2, Clock, Users, Wrench, FlaskConical, MapPin } from 'lucide-react';

export const Laboratories: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [labs, setLabs] = useState<Laboratory[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingLab, setEditingLab] = useState<Laboratory | null>(null);

  // Form states
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [capacity, setCapacity] = useState(30);
  const [openTime, setOpenTime] = useState('09:00');
  const [closeTime, setCloseTime] = useState('17:00');

  const fetchLabs = async () => {
    try {
      const res = await api.get('/laboratories');
      setLabs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLabs();
  }, []);

  const handleOpenAdd = () => {
    setEditingLab(null);
    setCode(`LAB-NEW-0${labs.length + 1}`);
    setName('');
    setLocation('');
    setCapacity(30);
    setOpenTime('09:00');
    setCloseTime('17:00');
    setIsModalOpen(true);
  };

  const handleOpenEdit = (lab: Laboratory) => {
    setEditingLab(lab);
    setCode(lab.code);
    setName(lab.name);
    setLocation(lab.location);
    setCapacity(lab.max_student_capacity);
    setOpenTime(lab.open_time);
    setCloseTime(lab.close_time);
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingLab) {
        await api.put(`/laboratories/${editingLab.id}`, {
          name,
          location,
          max_student_capacity: Number(capacity),
          open_time: openTime,
          close_time: closeTime,
        });
      } else {
        await api.post('/laboratories', {
          department_id: 1,
          code,
          name,
          location,
          max_student_capacity: Number(capacity),
          working_days: 'Monday to Friday',
          open_time: openTime,
          close_time: closeTime,
        });
      }
      setIsModalOpen(false);
      fetchLabs();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to save laboratory record');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Department Laboratories</h2>
          <p className="text-xs text-slate-400">
            Physical facilities, operational working hours and safe student capacities.
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={handleOpenAdd}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-navy-950 transition-colors shadow-lg shadow-cyan-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Add Laboratory</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {labs.map((lab) => (
          <div
            key={lab.id}
            className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4 hover:border-slate-700 transition-all"
          >
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                  {lab.code}
                </span>
                <h3 className="text-base font-bold text-white">{lab.name}</h3>
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <MapPin className="w-3.5 h-3.5 text-slate-500" />
                  <span>{lab.location}</span>
                </div>
              </div>
              {isAdmin && (
                <button
                  onClick={() => handleOpenEdit(lab)}
                  className="p-2 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-colors"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
              )}
            </div>

            <div className="grid grid-cols-3 gap-2 py-3 px-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
              <div>
                <p className="text-[10px] uppercase text-slate-500 font-medium">Safe Capacity</p>
                <p className="text-sm font-bold text-white mt-0.5">{lab.max_student_capacity} seats</p>
              </div>
              <div>
                <p className="text-[10px] uppercase text-slate-500 font-medium">Equipment</p>
                <p className="text-sm font-bold text-cyan-400 mt-0.5">{lab.equipment_count || 0} types</p>
              </div>
              <div>
                <p className="text-[10px] uppercase text-slate-500 font-medium">Experiments</p>
                <p className="text-sm font-bold text-blue-400 mt-0.5">{lab.experiment_count || 0} practicals</p>
              </div>
            </div>

            <div className="space-y-1.5 text-xs text-slate-400">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-slate-500">
                  <Clock className="w-3.5 h-3.5" /> Operating Hours:
                </span>
                <span className="font-mono text-slate-200">{lab.open_time} - {lab.close_time} ({lab.working_days})</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-slate-500">
                  <Users className="w-3.5 h-3.5" /> Lab Coordinator:
                </span>
                <span className="text-slate-200 font-medium">{lab.assigned_faculty_name || 'Dr. Rajesh Ramanathan'}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add / Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingLab ? 'Edit Laboratory Information' : 'Register New Laboratory'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Laboratory Code</label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              disabled={!!editingLab}
              required
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Laboratory Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
              placeholder="e.g. Advanced Embedded Systems Lab"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Campus Location</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              required
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
              placeholder="e.g. Block C, Room 201"
            />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Max Capacity</label>
              <input
                type="number"
                value={capacity}
                onChange={(e) => setCapacity(Number(e.target.value))}
                min="4"
                max="60"
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Opens At</label>
              <input
                type="text"
                value={openTime}
                onChange={(e) => setOpenTime(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Closes At</label>
              <input
                type="text"
                value={closeTime}
                onChange={(e) => setCloseTime(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white font-mono"
              />
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
              Save Laboratory
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
