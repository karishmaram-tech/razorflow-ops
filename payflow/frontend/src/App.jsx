import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import CommandCenter from './pages/CommandCenter';
import MetricsPage from './pages/MetricsPage';
import useStore from './store/useStore';

function AppLayout() {
  const { demoMode } = useStore();
  return (
    <div className="flex min-h-screen bg-pf-slate-950">
      <Sidebar demoMode={demoMode} />
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<CommandCenter />} />
          <Route path="/automations" element={<CommandCenter />} />
          <Route path="/processors" element={<CommandCenter />} />
          <Route path="/metrics" element={<MetricsPage />} />
          <Route path="/savings" element={<MetricsPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}
