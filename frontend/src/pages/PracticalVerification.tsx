import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { CompletionRecord, Experiment, StudentBatch } from '../types';
import { useAuth } from '../context/AuthContext';
import { Badge } from '../components/Badge';
import { CheckCircle2, XCircle, Clock, Search, Filter, ShieldCheck, UserCheck } from 'lucide-react';

export const PracticalVerification: React.FC = () => {
  const { user } = useAuth();
  const isFacultyOrAdmin = user?.role === 'faculty' || user?.role === 'admin';

  const [records, setRecords] = useState<CompletionRecord[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [batches, setBatches] = useState<StudentBatch[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedExp, setSelectedExp] = useState<string>('ALL');
  const [selectedBatch, setSelectedBatch] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [search, setSearch] = useState('');

  const fetchRecords = async () => {
    try {
      const [recRes, expRes, batchRes] = await Promise.all([
        api.get('/verification'),
        api.get('/experiments'),
        api.get('/batches')
      ]);
      setRecords(recRes.data);
      setExperiments(expRes.data);
      setBatches(batchRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, []);

  const handleVerify = async (recordId: number, status: 'Verified' | 'Rejected', notes?: string) => {
    try {
      await api.put(`/verification/verify/${recordId}`, {
        verification_status: status,
        assessment_notes: notes || (status === 'Verified' ? 'Practical demonstration verified and viva passed.' : 'Re-attempt required. Circuit wiring did not meet safety standard.')
      });
      fetchRecords();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Verification failed');
    }
  };

  const filtered = records.filter((r) => {
    const matchesSearch =
      r.student_name.toLowerCase().includes(search.toLowerCase()) ||
      r.student_id_number.toLowerCase().includes(search.toLowerCase()) ||
      r.experiment_name.toLowerCase().includes(search.toLowerCase());

    const matchesExp = selectedExp === 'ALL' || String(r.experiment_id) === selectedExp;
    const matchesBatch = selectedBatch === 'ALL' || String(r.batch_id) === selectedBatch;
    const matchesStatus = selectedStatus === 'ALL' || r.verification_status === selectedStatus;

    return matchesSearch && matchesExp && matchesBatch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">
            Faculty Practical Competency Verification Portal
          </h2>
          <p className="text-xs text-slate-400">
            Attendance alone does not count as proof of competence. Faculty verification required for institutional credit.
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono text-cyan-400">
          <ShieldCheck className="w-4 h-4" />
          <span>Strict Faculty Sign-off Enforced</span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-slate-900/80 border border-slate-800">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search student or experiment..."
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div>
          <select
            value={selectedExp}
            onChange={(e) => setSelectedExp(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Experiments</option>
            {experiments.map((e) => (
              <option key={e.id} value={String(e.id)}>{e.name}</option>
            ))}
          </select>
        </div>

        <div>
          <select
            value={selectedBatch}
            onChange={(e) => setSelectedBatch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Batches</option>
            {batches.map((b) => (
              <option key={b.id} value={String(b.id)}>{b.batch_code}</option>
            ))}
          </select>
        </div>

        <div>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Verification Statuses</option>
            <option value="Pending">Pending Review</option>
            <option value="Verified">Verified Competent</option>
            <option value="Rejected">Rejected / Re-attempt</option>
          </select>
        </div>
      </div>

      {/* Verification Records Table */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Student</th>
                <th className="px-4 py-3">Experiment</th>
                <th className="px-4 py-3">Participation</th>
                <th className="px-4 py-3">Verification Status</th>
                <th className="px-4 py-3">Assessment Notes</th>
                <th className="px-4 py-3 text-right">Faculty Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3">
                    <p className="font-semibold text-white">{r.student_name}</p>
                    <p className="text-[10px] text-cyan-400 font-mono">
                      {r.student_id_number} • {r.batch_code}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-medium text-slate-200">{r.experiment_name}</p>
                    <p className="text-[10px] text-slate-500 font-mono">{r.experiment_code}</p>
                  </td>
                  <td className="px-4 py-3">
                    <Badge label={r.participation_status} />
                  </td>
                  <td className="px-4 py-3">
                    <Badge label={r.verification_status} />
                  </td>
                  <td className="px-4 py-3 text-slate-400 max-w-xs truncate">
                    {r.assessment_notes || <span className="text-slate-600 italic">No notes</span>}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {isFacultyOrAdmin ? (
                      <div className="flex items-center justify-end gap-1.5">
                        {r.verification_status !== 'Verified' && (
                          <button
                            onClick={() => handleVerify(r.id, 'Verified')}
                            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-950 border border-emerald-700/60 text-emerald-400 hover:bg-emerald-900 transition-colors font-medium text-[11px]"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Verify</span>
                          </button>
                        )}
                        {r.verification_status !== 'Rejected' && (
                          <button
                            onClick={() => handleVerify(r.id, 'Rejected')}
                            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-950 border border-rose-700/60 text-rose-400 hover:bg-rose-900 transition-colors font-medium text-[11px]"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Reject</span>
                          </button>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-500 text-[11px] italic">Read Only</span>
                    )}
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
