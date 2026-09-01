import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import SettlementDetail from './pages/SettlementDetail';
import RefundDetail from './pages/RefundDetail';
import DisputeDetail from './pages/DisputeDetail';
import Metrics from './pages/Metrics';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/settlement/:id" element={<SettlementDetail />} />
        <Route path="/refund/:id" element={<RefundDetail />} />
        <Route path="/dispute/:id" element={<DisputeDetail />} />
        <Route path="/metrics" element={<Metrics />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
