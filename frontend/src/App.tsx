import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { Login } from './pages/Login';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Overview } from './pages/Overview';
import { Laboratories } from './pages/Laboratories';
import { Experiments } from './pages/Experiments';
import { EquipmentInventory } from './pages/EquipmentInventory';
import { StudentBatches } from './pages/StudentBatches';
import { FacultyManagement } from './pages/FacultyManagement';
import { CoverageAnalysis } from './pages/CoverageAnalysis';
import { PracticalVerification } from './pages/PracticalVerification';
import { ScheduleOptimization } from './pages/ScheduleOptimization';
import { RepairRecommendations } from './pages/RepairRecommendations';
import { DataImport } from './pages/DataImport';
import { Reports } from './pages/Reports';
import { StudentPortal } from './pages/StudentPortal';
import { HodAnalytics } from './pages/HodAnalytics';
import { SmartLabAllocation } from './pages/SmartLabAllocation';
import { StudentCompetencyDashboard } from './pages/StudentCompetencyDashboard';
import { ResourceIntelligence } from './pages/ResourceIntelligence';

export const AppContent: React.FC = () => {
  const { user, loading } = useAuth();
  const [currentTab, setCurrentTab] = useState('overview');

  if (loading) {
    return (
      <div className="min-h-screen bg-navy-950 flex items-center justify-center">
        <div className="flex items-center gap-3 text-cyan-400">
          <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-semibold tracking-wide">Initializing LABGAP System...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  const renderContent = () => {
    // If Student role, route overview directly to StudentPortal
    if (user.role === 'student') {
      if (currentTab === 'schedule') return <ScheduleOptimization />;
      if (currentTab === 'experiments') return <Experiments />;
      return <StudentPortal />;
    }

    // If HOD role, route overview to HodAnalytics
    if (user.role === 'hod' && currentTab === 'overview') {
      return <HodAnalytics />;
    }

    switch (currentTab) {
      case 'overview':
        return <Overview onNavigateTab={setCurrentTab} />;
      case 'laboratories':
        return <Laboratories />;
      case 'experiments':
        return <Experiments />;
      case 'equipment':
        return <EquipmentInventory />;
      case 'batches':
        return <StudentBatches />;
      case 'faculty':
        return <FacultyManagement />;
      case 'coverage':
        return <CoverageAnalysis />;
      case 'verification':
        return <PracticalVerification />;
      case 'schedule':
        return <ScheduleOptimization />;
      case 'smart-allocation':
        return <SmartLabAllocation />;
      case 'competency':
        return <StudentCompetencyDashboard />;
      case 'resource-intel':
        return <ResourceIntelligence />;
      case 'repairs':
        return <RepairRecommendations />;
      case 'import':
        return <DataImport />;
      case 'reports':
        return <Reports />;
      default:
        return <Overview onNavigateTab={setCurrentTab} />;
    }
  };

  return (
    <DashboardLayout currentTab={currentTab} onSelectTab={setCurrentTab}>
      {renderContent()}
    </DashboardLayout>
  );
};

export default function App() {
  return <AppContent />;
}
