import React, { useState } from 'react';
import { useAuth, DEMO_CREDENTIALS } from '../context/AuthContext';
import { UserRole } from '../types';
import { ShieldCheck, UserCheck, GraduationCap, Building2, ArrowRight, Lock, Mail } from 'lucide-react';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('admin@labgap.demo');
  const [password, setPassword] = useState('AdminPassword123!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const success = await login(email, password);
    if (!success) {
      setError('Invalid email or password. Please verify credentials.');
    }
    setLoading(false);
  };

  const handleQuickLogin = async (role: UserRole) => {
    const cred = DEMO_CREDENTIALS[role];
    setEmail(cred.email);
    setPassword(cred.pass);
    setLoading(true);
    setError(null);
    const success = await login(cred.email, cred.pass);
    if (!success) {
      setError(`Failed to sign in as ${cred.title}`);
    }
    setLoading(false);
  };

  const demoRoles = [
    { role: 'admin' as UserRole, title: 'Laboratory Administrator', desc: 'Full laboratory, inventory & scheduling control', icon: ShieldCheck, color: 'border-cyan-500/40 text-cyan-400 bg-cyan-950/40' },
    { role: 'faculty' as UserRole, title: 'Faculty / Lab Instructor', desc: 'Verify completion, record competencies', icon: UserCheck, color: 'border-blue-500/40 text-blue-400 bg-blue-950/40' },
    { role: 'student' as UserRole, title: 'Student Portal', desc: 'Personal laboratory schedule & verified progress', icon: GraduationCap, color: 'border-emerald-500/40 text-emerald-400 bg-emerald-950/40' },
    { role: 'hod' as UserRole, title: 'Head of Department', desc: 'Executive coverage audits & resource oversight', icon: Building2, color: 'border-purple-500/40 text-purple-400 bg-purple-950/40' },
  ];

  return (
    <div className="min-h-screen bg-navy-950 flex flex-col justify-center items-center p-6 relative overflow-hidden">
      {/* Subtle background glow */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-4xl relative z-10 space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-2">
            ELITE X Hackathon (ELX-P25) • Track 5
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
            LAB<span className="text-cyan-400">GAP</span>
          </h1>
          <p className="text-slate-400 text-sm max-w-xl mx-auto">
            Practical Learning Coverage & Resource Optimization System for Technical Institutions
          </p>
        </div>

        {/* 1-Click Fast Demo Role Selectors */}
        <div className="space-y-3">
          <p className="text-xs uppercase tracking-wider text-slate-400 font-semibold text-center">
            Select a Synthetic Demonstration Account (1-Click Sign In)
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {demoRoles.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.role}
                  type="button"
                  onClick={() => handleQuickLogin(item.role)}
                  className={`p-4 rounded-xl border text-left transition-all hover:scale-[1.02] active:scale-[0.98] ${item.color} shadow-lg shadow-black/30`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <Icon className="w-5 h-5" />
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-black/40">DEMO</span>
                  </div>
                  <h4 className="text-xs font-bold text-white leading-snug">{item.title}</h4>
                  <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{item.desc}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Manual Credentials Form */}
        <div className="max-w-md mx-auto bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-md">
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-rose-950/80 border border-rose-800 text-rose-300 text-xs">
                {error}
              </div>
            )}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                  placeholder="name@labgap.demo"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                  placeholder="••••••••••••"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-2.5 px-4 bg-gradient-to-r from-cyan-500 to-electric-600 hover:from-cyan-400 hover:to-electric-500 text-navy-950 font-bold rounded-xl text-xs transition-all shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In to Portal'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
