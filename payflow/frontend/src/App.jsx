import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LightSidebar from './components/light/Sidebar';
import LightDashboard from './pages/LightDashboard';
import PremiumDashboard from './pages/PremiumDashboard';
import Dashboard from './pages/Dashboard';
import AutomationDetail from './pages/AutomationDetail';
import Settings from './pages/Settings';
import FintechMobile from './pages/FintechMobile';
import SoftUIDashboard from './pages/SoftUIDashboard';
import FigmaDashboard from './pages/FigmaDashboard';

function AppLayout() {
  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg-page)' }}>
      <LightSidebar />
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<LightDashboard />} />
          <Route path="/dark" element={<PremiumDashboard />} />
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
    <div className="max-w-md mx-auto min-h-screen" style={{ background: 'var(--bg-page)', borderLeft: '1px solid var(--border)', borderRight: '1px solid var(--border)' }}>
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
        <Route path="/figma" element={<FigmaDashboard />} />
        <Route path="/*" element={<AppLayout />} />
      </Routes>
    </BrowserRouter>
  );
}
