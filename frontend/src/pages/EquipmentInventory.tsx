import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Equipment, Laboratory } from '../types';
import { useAuth } from '../context/AuthContext';
import { Modal } from '../components/Modal';
import { Badge } from '../components/Badge';
import { Wrench, Plus, Search, Filter, AlertTriangle, CheckCircle2, RefreshCw, Trash2, Edit } from 'lucide-react';

export const EquipmentInventory: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [equipmentList, setEquipmentList] = useState<Equipment[]>([]);
  const [labs, setLabs] = useState<Laboratory[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedLab, setSelectedLab] = useState<string>('ALL');
  const [selectedCondition, setSelectedCondition] = useState<string>('ALL');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEq, setEditingEq] = useState<Equipment | null>(null);

  // Form Fields
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [labId, setLabId] = useState<number>(1);
  const [desc, setDesc] = useState('');
  const [functional, setFunctional] = useState(0);
  const [partial, setPartial] = useState(0);
  const [damaged, setDamaged] = useState(0);
  const [maintenance, setMaintenance] = useState(0);
  const [maintenanceStatus, setMaintenanceStatus] = useState('Normal');

  const calculatedTotal = functional + partial + damaged + maintenance;

  const fetchData = async () => {
    try {
      const [eqRes, labRes] = await Promise.all([
        api.get('/equipment'),
        api.get('/laboratories')
      ]);
      setEquipmentList(eqRes.data);
      setLabs(labRes.data);
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
    setEditingEq(null);
    setCode(`EQ-DEMO-${equipmentList.length + 1}`);
    setName('');
    setLabId(labs[0]?.id || 1);
    setDesc('Standard laboratory test and measurement instrument.');
    setFunctional(8);
    setPartial(0);
    setDamaged(0);
    setMaintenance(0);
    setMaintenanceStatus('Normal');
    setIsModalOpen(true);
  };

  const handleOpenEdit = (eq: Equipment) => {
    setEditingEq(eq);
    setCode(eq.equipment_code);
    setName(eq.name);
    setLabId(eq.laboratory_id);
    setDesc(eq.description || '');
    setFunctional(eq.functional_quantity);
    setPartial(eq.partially_functional_quantity);
    setDamaged(eq.damaged_quantity);
    setMaintenance(eq.under_maintenance_quantity);
    setMaintenanceStatus(eq.maintenance_status);
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this equipment inventory record?')) return;
    try {
      await api.delete(`/equipment/${id}`);
      fetchData();
    } catch (err) {
      alert('Failed to delete equipment record');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (calculatedTotal <= 0) {
      alert('Total equipment quantity must be greater than zero.');
      return;
    }

    try {
      if (editingEq) {
        await api.put(`/equipment/${editingEq.id}`, {
          name,
          description: desc,
          laboratory_id: Number(labId),
          total_quantity: calculatedTotal,
          functional_quantity: Number(functional),
          partially_functional_quantity: Number(partial),
          damaged_quantity: Number(damaged),
          under_maintenance_quantity: Number(maintenance),
          maintenance_status: maintenanceStatus,
        });
      } else {
        await api.post('/equipment', {
          equipment_code: code,
          name,
          description: desc,
          laboratory_id: Number(labId),
          total_quantity: calculatedTotal,
          functional_quantity: Number(functional),
          partially_functional_quantity: Number(partial),
          damaged_quantity: Number(damaged),
          under_maintenance_quantity: Number(maintenance),
          maintenance_status: maintenanceStatus,
          repair_status: damaged > 0 ? 'Inspection Required' : 'None',
        });
      }
      setIsModalOpen(false);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update equipment inventory');
    }
  };

  // Filter list
  const filtered = equipmentList.filter((eq) => {
    const matchesSearch =
      eq.name.toLowerCase().includes(search.toLowerCase()) ||
      eq.equipment_code.toLowerCase().includes(search.toLowerCase());

    const matchesLab = selectedLab === 'ALL' || String(eq.laboratory_id) === selectedLab;

    let matchesCond = true;
    if (selectedCondition === 'DAMAGED') matchesCond = eq.damaged_quantity > 0;
    else if (selectedCondition === 'MAINTENANCE') matchesCond = eq.under_maintenance_quantity > 0;
    else if (selectedCondition === 'PARTIAL') matchesCond = eq.partially_functional_quantity > 0;
    else if (selectedCondition === 'FUNCTIONAL') matchesCond = eq.functional_quantity > 0;

    return matchesSearch && matchesLab && matchesCond;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Equipment Inventory & Health Status</h2>
          <p className="text-xs text-slate-400">
            Real-time functional condition breakdown. Non-functional units are strictly excluded from practical capacity.
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={handleOpenAdd}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-navy-950 transition-colors shadow-lg shadow-cyan-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Add Equipment</span>
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-4 rounded-xl bg-slate-900/80 border border-slate-800">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search equipment name or code..."
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
            value={selectedCondition}
            onChange={(e) => setSelectedCondition(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Operational Conditions</option>
            <option value="DAMAGED">Has Damaged Units</option>
            <option value="MAINTENANCE">Has Units Under Maintenance</option>
            <option value="PARTIAL">Has Partially Functional Units</option>
            <option value="FUNCTIONAL">Functional Units Available</option>
          </select>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Equipment</th>
                <th className="px-4 py-3">Laboratory</th>
                <th className="px-4 py-3 text-center">Total</th>
                <th className="px-4 py-3 text-center">Functional</th>
                <th className="px-4 py-3 text-center">Partially Func</th>
                <th className="px-4 py-3 text-center">Damaged</th>
                <th className="px-4 py-3 text-center">Maintenance</th>
                <th className="px-4 py-3">Status</th>
                {isAdmin && <th className="px-4 py-3 text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((eq) => (
                <tr key={eq.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3">
                    <p className="font-semibold text-white">{eq.name}</p>
                    <p className="text-[10px] text-cyan-400 font-mono">{eq.equipment_code}</p>
                  </td>
                  <td className="px-4 py-3 text-slate-300">{eq.laboratory_name}</td>
                  <td className="px-4 py-3 text-center font-bold text-white font-mono">{eq.total_quantity}</td>
                  <td className="px-4 py-3 text-center font-bold text-emerald-400 font-mono bg-emerald-950/20">
                    {eq.functional_quantity}
                  </td>
                  <td className="px-4 py-3 text-center text-blue-400 font-mono">
                    {eq.partially_functional_quantity}
                  </td>
                  <td className="px-4 py-3 text-center font-bold text-rose-400 font-mono bg-rose-950/20">
                    {eq.damaged_quantity}
                  </td>
                  <td className="px-4 py-3 text-center text-amber-400 font-mono bg-amber-950/20">
                    {eq.under_maintenance_quantity}
                  </td>
                  <td className="px-4 py-3">
                    <Badge label={eq.maintenance_status} />
                  </td>
                  {isAdmin && (
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleOpenEdit(eq)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-colors"
                        >
                          <Edit className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(eq.id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add / Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingEq ? 'Edit Equipment Condition & Quantities' : 'Add Equipment to Laboratory'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Equipment Code</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                disabled={!!editingEq}
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
            <label className="block text-xs font-medium text-slate-300 mb-1">Equipment Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
              placeholder="e.g. Digital Storage Oscilloscope 100MHz"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Specification / Description</label>
            <textarea
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              rows={2}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
            />
          </div>

          {/* Condition Breakdown */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-white">Condition Quantity Breakdown</span>
              <span className="text-xs font-mono font-bold text-cyan-400">Total: {calculatedTotal} units</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <div>
                <label className="block text-[10px] uppercase font-bold text-emerald-400 mb-1">Functional</label>
                <input
                  type="number"
                  value={functional}
                  onChange={(e) => setFunctional(Math.max(0, Number(e.target.value)))}
                  min="0"
                  required
                  className="w-full bg-slate-900 border border-emerald-700/60 rounded-xl px-2.5 py-1.5 text-xs text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-[10px] uppercase font-bold text-blue-400 mb-1">Partially Func</label>
                <input
                  type="number"
                  value={partial}
                  onChange={(e) => setPartial(Math.max(0, Number(e.target.value)))}
                  min="0"
                  required
                  className="w-full bg-slate-900 border border-blue-700/60 rounded-xl px-2.5 py-1.5 text-xs text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-[10px] uppercase font-bold text-rose-400 mb-1">Damaged</label>
                <input
                  type="number"
                  value={damaged}
                  onChange={(e) => setDamaged(Math.max(0, Number(e.target.value)))}
                  min="0"
                  required
                  className="w-full bg-slate-900 border border-rose-700/60 rounded-xl px-2.5 py-1.5 text-xs text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-[10px] uppercase font-bold text-amber-400 mb-1">Maintenance</label>
                <input
                  type="number"
                  value={maintenance}
                  onChange={(e) => setMaintenance(Math.max(0, Number(e.target.value)))}
                  min="0"
                  required
                  className="w-full bg-slate-900 border border-amber-700/60 rounded-xl px-2.5 py-1.5 text-xs text-white font-mono"
                />
              </div>
            </div>
            <p className="text-[10px] text-slate-500">
              Rule: Total quantity strictly equals sum of all condition units. Damaged and maintenance units are automatically excluded from session capacity.
            </p>
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
              Save Equipment
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
