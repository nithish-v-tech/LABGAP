import React from 'react';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  FlaskConical,
  Wrench,
  Building,
  Users,
  GraduationCap,
  UploadCloud,
  Cpu,
  CalendarCheck,
  CheckCircle2,
  AlertTriangle,
  FileText,
  BarChart3,
  Sparkles,
  Award,
  Lightbulb
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const { user } = useAuth();
  const role = user?.role || 'admin';

  const allNavItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard, roles: ['admin', 'faculty', 'student', 'hod'] },
    { id: 'experiments', label: 'Experiments', icon: FlaskConical, roles: ['admin', 'faculty', 'student'] },
    { id: 'equipment', label: 'Equipment Inventory', icon: Wrench, roles: ['admin', 'hod'] },
    { id: 'laboratories', label: 'Laboratories', icon: Building, roles: ['admin', 'hod'] },
    { id: 'batches', label: 'Student Batches', icon: Users, roles: ['admin', 'faculty'] },
    { id: 'faculty', label: 'Faculty Directory', icon: GraduationCap, roles: ['admin'] },
    { id: 'coverage', label: 'Coverage Analysis', icon: Cpu, roles: ['admin', 'hod'] },
    { id: 'verification', label: 'Practical Verification', icon: CheckCircle2, roles: ['admin', 'faculty'] },
    { id: 'smart-allocation', label: 'Smart Lab Allocation', icon: Sparkles, roles: ['admin', 'hod'] },
    { id: 'competency', label: 'Student Competencies', icon: Award, roles: ['admin', 'faculty', 'hod'] },
    { id: 'resource-intel', label: 'Resource Intelligence', icon: Lightbulb, roles: ['admin', 'hod'] },
    { id: 'schedule', label: 'Schedule Optimization', icon: CalendarCheck, roles: ['admin', 'faculty', 'student'] },
    { id: 'repairs', label: 'Repair Recommendations', icon: AlertTriangle, roles: ['admin', 'hod'] },
    { id: 'import', label: 'Data Import (CSV)', icon: UploadCloud, roles: ['admin'] },
    { id: 'reports', label: 'Reports & Audits', icon: FileText, roles: ['admin', 'faculty', 'hod'] },
  ];

  const visibleItems = allNavItems.filter((item) => item.roles.includes(role));

  return (
    <aside className="w-64 flex-shrink-0 bg-slate-900/95 border-r border-slate-800 flex flex-col justify-between p-4 min-h-[calc(100vh-61px)]">
      <div className="space-y-6">
        {/* Navigation Category Label */}
        <div>
          <p className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
            {role === 'admin' ? 'Administration & Planning' : role === 'faculty' ? 'Faculty Portal' : role === 'student' ? 'Student Portal' : 'Executive Oversight'}
          </p>
          <nav className="space-y-1">
            {visibleItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-950/90 to-blue-950/60 text-cyan-400 border border-cyan-500/30 font-semibold shadow-inner'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Institutional Metadata Footer */}
      <div className="pt-4 border-t border-slate-800/80">
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
          <p className="text-[11px] font-semibold text-slate-300">Apex Institute of Tech</p>
          <p className="text-[10px] text-slate-500 mt-0.5">ELITE X Hackathon (ELX-P25)</p>
          <div className="mt-2 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[10px] text-emerald-400 font-mono">System Operational</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
