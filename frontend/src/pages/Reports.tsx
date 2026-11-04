import React, { useEffect, useState } from 'react';
import { api, API_BASE_URL } from '../services/api';
import { FileText, Download, Printer, RefreshCw, Calendar, CheckCircle } from 'lucide-react';
import { Badge } from '../components/Badge';

export const Reports: React.FC = () => {
  const [reportType, setReportType] = useState<'coverage' | 'equipment-shortages' | 'student-gaps'>('coverage');
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/reports/${reportType}`);
      setReportData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [reportType]);

  const handleExportCsv = () => {
    window.open(`${API_BASE_URL}/reports/${reportType}?format=csv`, '_blank');
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 to-navy-900 border border-slate-800 shadow-xl">
        <div className="space-y-1">
          <h2 className="text-xl font-bold text-white tracking-wide">
            Institutional Practical Competency & Resource Audit Reports
          </h2>
          <p className="text-xs text-slate-400">
            Export compliant accreditation reports with verified mathematical capacity explanations and timestamps.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCsv}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-navy-950 transition-colors shadow-lg shadow-cyan-500/20"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Report</span>
          </button>
        </div>
      </div>

      {/* Select Report View */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setReportType('coverage')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            reportType === 'coverage'
              ? 'bg-cyan-500 text-navy-950 shadow-md shadow-cyan-500/20'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          Curriculum Coverage Report
        </button>
        <button
          onClick={() => setReportType('equipment-shortages')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            reportType === 'equipment-shortages'
              ? 'bg-cyan-500 text-navy-950 shadow-md shadow-cyan-500/20'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          Equipment Shortages & Repairs
        </button>
        <button
          onClick={() => setReportType('student-gaps')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            reportType === 'student-gaps'
              ? 'bg-cyan-500 text-navy-950 shadow-md shadow-cyan-500/20'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          Student Learning Gap Audit
        </button>
      </div>

      {/* Report Canvas */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl space-y-4 printable-area">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-2">
          <div>
            <h3 className="text-base font-bold text-white">{reportData?.report_title || 'Institutional Audit'}</h3>
            <p className="text-xs text-slate-400">Apex Institute of Technology & Engineering • EEE Department</p>
          </div>
          <div className="text-right text-[11px] text-slate-400 font-mono">
            <p>Timestamp: {reportData?.generated_at}</p>
            <p>Auditor: {reportData?.generated_by}</p>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-cyan-400 text-xs">Generating report...</div>
        ) : reportType === 'coverage' ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
                <tr>
                  <th className="px-3 py-2.5">Code</th>
                  <th className="px-3 py-2.5">Practical Name</th>
                  <th className="px-3 py-2.5">Facility</th>
                  <th className="px-3 py-2.5">Coverage Status</th>
                  <th className="px-3 py-2.5 text-center">Active Stations</th>
                  <th className="px-3 py-2.5 text-center">Verified / Gap</th>
                  <th className="px-3 py-2.5">Algorithmic Proof</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {reportData?.data?.map((row: any, i: number) => (
                  <tr key={i} className="hover:bg-slate-800/20">
                    <td className="px-3 py-2.5 font-mono text-cyan-400">{row.experiment_code}</td>
                    <td className="px-3 py-2.5 font-medium text-white">{row.experiment_name}</td>
                    <td className="px-3 py-2.5 text-slate-300">{row.laboratory}</td>
                    <td className="px-3 py-2.5"><Badge label={row.classification} /></td>
                    <td className="px-3 py-2.5 text-center font-mono">{row.active_stations}</td>
                    <td className="px-3 py-2.5 text-center font-mono">
                      <span className="text-emerald-400">{row.verified_completed}</span> / <span className="text-rose-400">{row.remaining_learning_gap}</span>
                    </td>
                    <td className="px-3 py-2.5 text-[11px] text-slate-400 max-w-sm">{row.explanation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : reportType === 'equipment-shortages' ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
                <tr>
                  <th className="px-3 py-2.5">Priority</th>
                  <th className="px-3 py-2.5">Equipment</th>
                  <th className="px-3 py-2.5">Facility</th>
                  <th className="px-3 py-2.5 text-center">Damaged / Maint</th>
                  <th className="px-3 py-2.5 text-center">Capacity Gain</th>
                  <th className="px-3 py-2.5">Decision Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {reportData?.data?.map((row: any, i: number) => (
                  <tr key={i} className="hover:bg-slate-800/20">
                    <td className="px-3 py-2.5"><Badge label={row.priority} /></td>
                    <td className="px-3 py-2.5 font-medium text-white">{row.equipment_name} ({row.equipment_code})</td>
                    <td className="px-3 py-2.5 text-slate-300">{row.laboratory_name}</td>
                    <td className="px-3 py-2.5 text-center font-mono text-rose-400 font-bold">{row.repairable_units}</td>
                    <td className="px-3 py-2.5 text-center font-mono text-emerald-400 font-bold">+{row.potential_capacity_gain}</td>
                    <td className="px-3 py-2.5 text-[11px] text-slate-400 max-w-sm">{row.reason_for_priority}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
                <tr>
                  <th className="px-3 py-2.5">Experiment Code</th>
                  <th className="px-3 py-2.5">Experiment Title</th>
                  <th className="px-3 py-2.5 text-center">Total Assigned</th>
                  <th className="px-3 py-2.5 text-center">Verified Competent</th>
                  <th className="px-3 py-2.5 text-center">Unverified Gap</th>
                  <th className="px-3 py-2.5 text-center">Gap %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {reportData?.data?.map((row: any, i: number) => (
                  <tr key={i} className="hover:bg-slate-800/20">
                    <td className="px-3 py-2.5 font-mono text-cyan-400">{row.experiment_code}</td>
                    <td className="px-3 py-2.5 font-medium text-white">{row.experiment_name}</td>
                    <td className="px-3 py-2.5 text-center font-mono font-bold text-white">{row.total_assigned}</td>
                    <td className="px-3 py-2.5 text-center font-mono text-emerald-400 font-bold">{row.verified_completed}</td>
                    <td className="px-3 py-2.5 text-center font-mono text-rose-400 font-bold">{row.unverified_learning_gap}</td>
                    <td className="px-3 py-2.5 text-center font-mono text-amber-400 font-bold">{row.gap_percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
