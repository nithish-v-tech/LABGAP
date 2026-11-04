import React, { useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Download, UploadCloud, AlertTriangle, CheckCircle2, FileText, ArrowRight } from 'lucide-react';

export const DataImport: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [activeTab, setActiveTab] = useState<'experiments' | 'equipment' | 'students' | 'batches'>('experiments');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleDownloadTemplate = async (entity: string) => {
    try {
      const res = await api.get(`/csv/template/${entity}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${entity}_template.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Failed to download template');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      alert('Please select a CSV file to upload.');
      return;
    }

    setUploading(true);
    setResult(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post(`/csv/upload/${activeTab}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(res.data);
      setFile(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'CSV upload and validation failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 to-navy-900 border border-slate-800 shadow-xl space-y-1">
        <h2 className="text-xl font-bold text-white tracking-wide">
          Institutional CSV Data Management & Ingestion
        </h2>
        <p className="text-xs text-slate-400">
          Bulk import experiments, equipment inventory, student rosters, and batches with strict automated validation.
        </p>
      </div>

      {/* Entity Selector Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        {(['experiments', 'equipment', 'students', 'batches'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => {
              setActiveTab(tab);
              setResult(null);
              setFile(null);
            }}
            className={`px-4 py-2 rounded-xl text-xs font-semibold capitalize transition-all ${
              activeTab === tab
                ? 'bg-cyan-500 text-navy-950 shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Template Download & Specs */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white capitalize">{activeTab} CSV Template</h3>
            <button
              onClick={() => handleDownloadTemplate(activeTab)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Template</span>
            </button>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Ensure all uploaded files follow the official institutional schema. Automated checks validate non-negative numbers, primary key constraints, and foreign key integrity.
          </p>

          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 text-xs">
            <span className="font-semibold text-slate-300">Strict Validation Rules Enforced:</span>
            <ul className="list-disc pl-4 space-y-1 text-slate-400 text-[11px]">
              <li>Rejection of negative quantities or durations</li>
              <li>Verification that condition sums equal total equipment quantity</li>
              <li>Detection of duplicate codes or unregistered student IDs</li>
              <li>Detailed line-by-line rejection reports without silent discarding</li>
            </ul>
          </div>
        </div>

        {/* Right: Upload Box & Results */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
          <h3 className="text-sm font-semibold text-white">Upload and Ingest CSV Data</h3>

          <form onSubmit={handleUpload} className="space-y-4">
            <div className="border-2 border-dashed border-slate-700 rounded-2xl p-6 text-center hover:border-cyan-500/60 transition-colors bg-slate-950/40">
              <UploadCloud className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
              <label className="cursor-pointer">
                <span className="text-xs font-semibold text-cyan-400 hover:underline">
                  Click to select CSV file
                </span>
                <span className="text-xs text-slate-400"> or drag and drop</span>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
              {file && (
                <div className="mt-2 text-xs font-mono text-emerald-400 font-medium">
                  Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={uploading || !file}
              className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                uploading || !file
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-cyan-500 hover:bg-cyan-400 text-navy-950 shadow-lg shadow-cyan-500/20'
              }`}
            >
              <UploadCloud className="w-4 h-4" />
              <span>{uploading ? 'Validating and Ingesting...' : `Validate & Ingest ${activeTab}`}</span>
            </button>
          </form>

          {/* Upload Results & Error Logs */}
          {result && (
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-white">Ingestion Results Summary</span>
                <span className="font-mono text-slate-400">{result.file_name}</span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                  <p className="text-[10px] uppercase text-slate-500">Total Rows</p>
                  <p className="text-base font-bold text-white mt-0.5">{result.total_rows}</p>
                </div>
                <div className="p-2 rounded-lg bg-emerald-950/40 border border-emerald-800/60">
                  <p className="text-[10px] uppercase text-emerald-400">Successful</p>
                  <p className="text-base font-bold text-emerald-400 mt-0.5">{result.successful_rows}</p>
                </div>
                <div className="p-2 rounded-lg bg-rose-950/40 border border-rose-800/60">
                  <p className="text-[10px] uppercase text-rose-400">Rejected</p>
                  <p className="text-base font-bold text-rose-400 mt-0.5">{result.rejected_rows}</p>
                </div>
              </div>

              {result.errors && result.errors.length > 0 && (
                <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-800 text-xs space-y-1">
                  <p className="font-semibold text-rose-400">Rejection Diagnostics & Errors:</p>
                  <ul className="list-disc pl-4 space-y-0.5 text-rose-300 text-[11px] max-h-32 overflow-y-auto">
                    {result.errors.map((err: string, i: number) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
