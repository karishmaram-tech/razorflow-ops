import { BrowserRouter, Routes, Route } from 'react-router-dom';
import PremiumSidebar from './components/premium/Sidebar';
import PremiumDashboard from './pages/PremiumDashboard';
import Dashboard from './pages/Dashboard';
import AutomationDetail from './pages/AutomationDetail';
import Settings from './pages/Settings';
import FintechMobile from './pages/FintechMobile';
import SoftUIDashboard from './pages/SoftUIDashboard';

function AppLayout() {
  return (
    <div className="flex min-h-screen" style={{ background: 'var(--pf-bg)' }}>
      <PremiumSidebar />
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<PremiumDashboard />} />
          <Route path="/classic" element={<Dashboard />} />
          <Route path="/automations/:id" element={<AutomationDetail />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/softui" element={<SoftUIDashboard />} />
        </Routes>
      </main>
    </div>
  );
}

function MobileLayout() {
  return (
    <div className="max-w-md mx-auto min-h-screen border-x" style={{ background: 'var(--pf-bg)', borderColor: 'var(--pf-border)' }}>
      <Routes>
        <Route path="/" element={<FintechMobile />} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/mobile/*" element={<MobileLayout />} />
        <Route path="/*" element={<AppLayout />} />
      </Routes>
    </BrowserRouter>
  );
}
