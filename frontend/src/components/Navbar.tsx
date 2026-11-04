import React, { useState } from 'react';
import { useAuth, DEMO_CREDENTIALS } from '../context/AuthContext';
import { UserRole } from '../types';
import { LogOut, RotateCcw, ShieldCheck, UserCheck, GraduationCap, Building2 } from 'lucide-react';
import { api } from '../services/api';

export const Navbar: React.FC = () => {
  const { user, logout, switchDemoRole } = useAuth();
  const [resetting, setResetting] = useState(false);
  const [resetMsg, setResetMsg] = useState<string | null>(null);

  const handleResetDemo = async () => {
    if (!window.confirm('Reset database to clean benchmark demonstration dataset? (15 experiments, 20 equipment, 68 students)')) {
      return;
    }
    setResetting(true);
    try {
      await api.post('/demo/reset');
      setResetMsg('Benchmark demo data restored!');
      setTimeout(() => {
        setResetMsg(null);
        window.location.reload();
      }, 1200);
    } catch (err) {
      alert('Failed to reset demo data');
    } finally {
      setResetting(false);
    }
  };

  const roleIcons = {
    admin: ShieldCheck,
    faculty: UserCheck,
    student: GraduationCap,
    hod: Building2,
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-6 py-3">
      <div className="flex items-center justify-between">
        {/* Left: Department & Context */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-600 to-electric-500 flex items-center justify-center font-black text-navy-950 text-lg shadow-lg shadow-cyan-500/20">
            L
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white tracking-wide text-sm">LABGAP</span>
              <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                Round 1 Prototype
              </span>
            </div>
            <p className="text-xs text-slate-400 truncate max-w-md">
              {user?.department_name || 'Department of Electrical & Electronics Engineering'}
            </p>
          </div>
        </div>

        {/* Center: Live Role Switcher for Hackathon Demonstrations */}
        <div className="hidden lg:flex items-center gap-1.5 p-1 bg-slate-950/80 rounded-xl border border-slate-800">
          {(['admin', 'faculty', 'student', 'hod'] as UserRole[]).map((r) => {
            const Icon = roleIcons[r];
            const isActive = user?.role === r;
            return (
              <button
                key={r}
                onClick={() => switchDemoRole(r)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-500 text-navy-950 font-semibold shadow-md shadow-cyan-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
                title={`Switch demo login to ${DEMO_CREDENTIALS[r].title}`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span className="capitalize">{r}</span>
              </button>
            );
          })}
        </div>

        {/* Right: Reset Demo, User & Logout */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleResetDemo}
            disabled={resetting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/60 transition-colors"
            title="Reset synthetic dataset"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin text-cyan-400' : ''}`} />
            <span className="hidden sm:inline">{resetMsg || 'Reset Demo Data'}</span>
          </button>

          <div className="h-6 w-px bg-slate-800 hidden sm:block" />

          <div className="flex items-center gap-2.5">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-semibold text-white leading-tight">{user?.full_name}</p>
              <p className="text-[10px] text-cyan-400 font-mono capitalize">{user?.role} view</p>
            </div>
            <button
              onClick={logout}
              className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
