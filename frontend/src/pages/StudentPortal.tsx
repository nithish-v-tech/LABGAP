import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Badge } from '../components/Badge';
import { GraduationCap, CheckCircle2, Clock, Calendar, AlertOctagon, BookOpen, ShieldAlert } from 'lucide-react';

export const StudentPortal: React.FC = () => {
  const { user } = useAuth();
  const studentId = user?.student_id || 1; // Default to synthetic student 1 (Aarav Patel)

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchStudentData = async () => {
    try {
      const res = await api.get(`/students/portal/${studentId}`);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudentData();
  }, [studentId]);

  if (loading) {
    return <div className="p-8 text-center text-cyan-400 text-xs">Loading student curriculum portal...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Student Profile Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 to-navy-900 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-cyan-950 border border-cyan-800/80 flex items-center justify-center text-cyan-400 font-bold text-xl shadow-lg shadow-cyan-500/20">
            <GraduationCap className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white">{data?.name}</h2>
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-black/40 text-cyan-400 border border-slate-700">
                {data?.student_id_number}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {data?.department_name} • Cohort: <strong className="text-white">{data?.batch_code}</strong> ({data?.batch_name})
            </p>
          </div>
        </div>

        {/* Progress Pill */}
        <div className="flex items-center gap-4 p-3 rounded-xl bg-slate-950/80 border border-slate-800">
          <div>
            <p className="text-[10px] uppercase text-slate-500 font-semibold">Practical Completion</p>
            <p className="text-lg font-bold text-emerald-400">{data?.completion_rate_percentage}%</p>
          </div>
          <div className="h-8 w-px bg-slate-800" />
          <div>
            <p className="text-[10px] uppercase text-slate-500 font-semibold">Verified / Total</p>
            <p className="text-lg font-bold text-white">
              {data?.verified_completed_count} / {data?.total_assigned_experiments}
            </p>
          </div>
        </div>
      </div>

      {/* Security notice */}
      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
        <ShieldAlert className="w-4 h-4 text-cyan-400 flex-shrink-0" />
        <span>
          Institutional Rule: Students cannot self-approve practical experiments. All competency credits require live lab session sign-off by the faculty instructor.
        </span>
      </div>

      {/* Assigned Experiments and Competency Status */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">Curriculum Practical Experiments ({data?.experiments?.length || 0})</h3>
          <span className="text-xs text-slate-400">{data?.pending_experiments_count} experiments pending completion</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data?.experiments?.map((exp: any) => (
            <div
              key={exp.experiment_id}
              className={`p-4 rounded-xl border transition-all space-y-2.5 ${
                exp.is_verified
                  ? 'bg-emerald-950/20 border-emerald-600/40'
                  : 'bg-slate-950/60 border-slate-800'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="font-mono text-[10px] text-cyan-400 font-bold px-1.5 py-0.5 rounded bg-black/40 border border-slate-800">
                    {exp.experiment_code}
                  </span>
                  <h4 className="text-xs font-bold text-white mt-1">{exp.experiment_name}</h4>
                  <p className="text-[11px] text-slate-400">{exp.laboratory_name}</p>
                </div>
                <Badge label={exp.status_badge} />
              </div>

              <div className="text-[11px] text-slate-400 border-t border-slate-800/80 pt-2 flex items-center justify-between">
                <span>Competency: <strong className="text-slate-300">{exp.practical_competency}</strong></span>
                <span>{exp.duration_hours} hrs</span>
              </div>

              {exp.instructor_notes && (
                <div className="p-2 rounded bg-slate-900 text-[10px] text-slate-400 italic">
                  Faculty feedback: "{exp.instructor_notes}"
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Upcoming Personal Laboratory Sessions */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
        <h3 className="text-sm font-semibold text-white">Upcoming Practical Rotations for {data?.batch_code}</h3>
        {data?.upcoming_schedules && data.upcoming_schedules.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {data.upcoming_schedules.map((s: any) => (
              <div key={s.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                <div className="flex items-center justify-between text-cyan-400 font-mono text-[11px]">
                  <span>{s.date}</span>
                  <span>{s.start_time} - {s.end_time}</span>
                </div>
                <h4 className="font-bold text-white text-xs">{s.experiment_name}</h4>
                <p className="text-slate-400 text-[11px]">{s.laboratory_name}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-500 text-xs italic">No upcoming lab sessions scheduled for this week.</p>
        )}
      </div>
    </div>
  );
};
