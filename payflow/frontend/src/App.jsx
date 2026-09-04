import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import AutomationDetail from './pages/AutomationDetail';
import Settings from './pages/Settings';
import FintechMobile from './pages/FintechMobile';
import SoftUIDashboard from './pages/SoftUIDashboard';

function AppLayout() {
  return (
    <div className="flex min-h-screen bg-[var(--bg-dark)]">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/automations/:id" element={<AutomationDetail />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}

function MobileLayout() {
  return (
    <div className="max-w-md mx-auto min-h-screen bg-[var(--bg-dark)] border-x border-[var(--border-subtle)]">
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
        <Route path="/softui" element={<SoftUIDashboard />} />
        <Route path="/*" element={<AppLayout />} />
      </Routes>
    </BrowserRouter>
  );
}
