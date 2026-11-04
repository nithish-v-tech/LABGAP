import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Faculty, Laboratory } from '../types';
import { useAuth } from '../context/AuthContext';
import { GraduationCap, Mail, Building, CheckCircle2, Users, Plus } from 'lucide-react';

export const FacultyManagement: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [faculty, setFaculty] = useState<Faculty[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchFaculty = async () => {
    try {
      const res = await api.get('/faculty');
      setFaculty(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFaculty();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Faculty Instructors & Verifiers</h2>
          <p className="text-xs text-slate-400">
            Authorized academic instructors responsible for lab rotations, student assessment and practical verification.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {faculty.map((f) => (
          <div
            key={f.id}
            className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4"
          >
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <span className="font-mono text-xs text-cyan-400 font-semibold px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800/60">
                  {f.faculty_code}
                </span>
                <h3 className="text-base font-bold text-white mt-1">{f.name}</h3>
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <Mail className="w-3.5 h-3.5 text-slate-500" />
                  <span>{f.email}</span>
                </div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Assigned Facility:</span>
                <span className="text-slate-200 font-medium">{f.assigned_laboratory_name || 'Electronics Lab'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Assigned Cohorts:</span>
                <span className="text-cyan-400 font-bold">{f.assigned_batches_count || 1} Batches</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Pending Verifications:</span>
                <span className="text-amber-400 font-bold">{f.pending_verifications_count || 0} Submissions</span>
              </div>
            </div>

            <div className="pt-2 text-[11px] text-slate-500 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Authorized to verify practical competence records</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
