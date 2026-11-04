import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { StudentBatch } from '../types';
import { useAuth } from '../context/AuthContext';
import {
  Award,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Users,
  Search,
  Filter,
  ChevronDown,
  ChevronUp,
  FileCheck2,
  XCircle,
  HelpCircle
} from 'lucide-react';
import { Badge } from '../components/Badge';

export const StudentCompetencyDashboard: React.FC = () => {
  const { user } = useAuth();
  const isFacultyOrAdmin = user?.role === 'faculty' || user?.role === 'admin';

  const [batches, setBatches] = useState<StudentBatch[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<number>(0);
  const [competencyData, setCompetencyData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedStudentId, setExpandedStudentId] = useState<number | null>(null);

  const fetchBatches = async () => {
    try {
      const res = await api.get('/batches');
      setBatches(res.data);
      if (res.data.length > 0) {
        setSelectedBatchId(res.data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchCompetencyData = async (batchId: number) => {
    setLoading(true);
    try {
      const res = await api.get('/analysis/competency-matrix', {
        params: batchId ? { batch_id: batchId } : {}
      });
      setCompetencyData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBatches();
  }, []);

  useEffect(() => {
    if (selectedBatchId !== undefined) {
      fetchCompetencyData(selectedBatchId);
    }
  }, [selectedBatchId]);

  const summary = competencyData?.cohort_summary || {
    total_students: 0,
    average_competency_rate: 0,
    fully_competent_count: 0,
    students_with_gaps_count: 0,
    at_risk_students_count: 0
  };

  const students = competencyData?.students || [];
  const filteredStudents = students.filter((s: any) =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.student_id_number.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-navy-900 to-emerald-950 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-bold text-white tracking-wide">
              Student Practical Competency Tracking
            </h2>
            <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px] font-mono uppercase">
              Faculty Verified
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Strict competency accounting: attendance does NOT equal competency. Only instructor-verified practical completions close learning gaps.
          </p>
        </div>
      </div>

      {/* Cohort KPI Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-lg space-y-1">
          <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-cyan-400" /> Total Students
          </p>
          <p className="text-2xl font-bold text-white font-mono">{summary.total_students}</p>
          <p className="text-[10px] text-slate-500">Enrolled in Cohort</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-lg space-y-1">
          <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5 text-emerald-400" /> Average Verified Rate
          </p>
          <p className="text-2xl font-bold text-emerald-400 font-mono">
            {summary.average_competency_rate}%
          </p>
          <p className="text-[10px] text-slate-500">Faculty-Certified Competencies</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-lg space-y-1">
          <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Fully Competent
          </p>
          <p className="text-2xl font-bold text-white font-mono">{summary.fully_competent_count}</p>
          <p className="text-[10px] text-emerald-400/80">Zero Practical Gaps Remaining</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-lg space-y-1">
          <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" /> Students with Gaps
          </p>
          <p className="text-2xl font-bold text-rose-400 font-mono">{summary.students_with_gaps_count}</p>
          <p className="text-[10px] text-rose-300/80">{summary.at_risk_students_count} labeled At-Risk</p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-semibold text-slate-300">Cohort:</span>
          <select
            value={selectedBatchId}
            onChange={(e) => setSelectedBatchId(Number(e.target.value))}
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value={0}>All Batches (Full Department)</option>
            {batches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.batch_code} — {b.batch_name}
              </option>
            ))}
          </select>
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search student or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {/* Student Competency List */}
      {loading ? (
        <div className="p-12 text-center text-cyan-400">
          <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <span className="text-xs">Computing practical competency metrics...</span>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredStudents.length > 0 ? (
            filteredStudents.map((s: any) => {
              const isExpanded = expandedStudentId === s.student_id;
              const isProficient = s.status_level === 'Proficient';
              const isProgressing = s.status_level === 'Progressing';

              return (
                <div
                  key={s.student_id}
                  className="rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all overflow-hidden"
                >
                  {/* Summary Bar */}
                  <div
                    onClick={() => setExpandedStudentId(isExpanded ? null : s.student_id)}
                    className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer select-none"
                  >
                    <div className="space-y-0.5 min-w-[200px]">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-bold text-white">{s.name}</h4>
                        <span className="font-mono text-[10px] text-cyan-400 px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-800">
                          {s.student_id_number}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400">{s.email} • {s.batch_code}</p>
                    </div>

                    {/* Progress Bar */}
                    <div className="flex-1 max-w-xs space-y-1">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-400">Verified Competency:</span>
                        <span className="font-mono font-bold text-white">{s.competency_percentage}%</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden">
                        <div
                          className={`h-full transition-all duration-500 ${
                            isProficient
                              ? 'bg-emerald-500'
                              : isProgressing
                              ? 'bg-amber-500'
                              : 'bg-rose-500'
                          }`}
                          style={{ width: `${s.competency_percentage}%` }}
                        />
                      </div>
                    </div>

                    {/* Status & Gaps */}
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-xs font-bold text-white">
                          {s.verified_practicals} / {s.total_assigned} Practicals
                        </p>
                        <p className="text-[10px] text-amber-400">
                          {s.remaining_learning_gap} Gap(s) Remaining
                        </p>
                      </div>

                      <span
                        className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                          isProficient
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : isProgressing
                            ? 'bg-amber-950 text-amber-400 border border-amber-800'
                            : 'bg-rose-950 text-rose-400 border border-rose-800'
                        }`}
                      >
                        {s.status_level}
                      </span>

                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Experiment Checklist */}
                  {isExpanded && (
                    <div className="p-4 bg-slate-950/80 border-t border-slate-800 space-y-3">
                      <h5 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                        Curriculum Practicals Verification Breakdown
                      </h5>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead>
                            <tr className="border-b border-slate-800 text-[10px] font-bold text-slate-500 uppercase">
                              <th className="pb-2">Code</th>
                              <th className="pb-2">Experiment</th>
                              <th className="pb-2">Competency Domain</th>
                              <th className="pb-2">Participation</th>
                              <th className="pb-2">Faculty Verification</th>
                              <th className="pb-2">Assessment Notes</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60">
                            {s.experiments.map((exp: any) => (
                              <tr key={exp.experiment_id} className="hover:bg-slate-900/50">
                                <td className="py-2.5 font-mono text-cyan-400">{exp.experiment_code}</td>
                                <td className="py-2.5 font-semibold text-white">{exp.experiment_name}</td>
                                <td className="py-2.5 text-slate-300">{exp.practical_competency}</td>
                                <td className="py-2.5">
                                  <Badge label={exp.participation_status} />
                                </td>
                                <td className="py-2.5">
                                  {exp.is_verified ? (
                                    <span className="flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                                      <CheckCircle2 className="w-3.5 h-3.5" /> Verified Competent
                                    </span>
                                  ) : (
                                    <span className="flex items-center gap-1 text-amber-400 font-semibold text-[11px]">
                                      <Clock className="w-3.5 h-3.5" /> Pending Faculty Viva
                                    </span>
                                  )}
                                </td>
                                <td className="py-2.5 text-slate-400 italic">
                                  {exp.assessment_notes || 'No assessment notes recorded'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="p-8 text-center text-slate-500 text-xs italic">
              No students match the current cohort or search filter.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
