import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { RecoveryProvider } from './lib/RecoveryContext';
import Shell from './components/layout/Shell';
import Homepage from './pages/Homepage';
import RecoveryDashboard from './pages/RecoveryDashboard';
import PaymentDetail from './pages/PaymentDetail';
import Strategies from './pages/Strategies';
import Analytics from './pages/Analytics';
import ControlCenter from './pages/ControlCenter';
import AuditLog from './pages/AuditLog';
import Sandbox from './pages/Sandbox';

export default function App() {
  return (
    <RecoveryProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Homepage />} />
          <Route path="/app" element={<Shell />}>
            <Route index element={<RecoveryDashboard />} />
            <Route path="payments/:id" element={<PaymentDetail />} />
            <Route path="strategies" element={<Strategies />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="control-center" element={<ControlCenter />} />
            <Route path="audit-log" element={<AuditLog />} />
            <Route path="sandbox" element={<Sandbox />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </RecoveryProvider>
  );
}
