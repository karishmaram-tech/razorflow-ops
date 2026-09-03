import { Link, useLocation } from 'react-router-dom';

export default function Navbar({ connected = true, demoMode = false }) {
  const location = useLocation();

  const navLinks = [
    { path: '/', label: 'Dashboard' },
    { path: '/metrics', label: 'Metrics' },
  ];

  return (
    <nav className="bg-white border-b border-gray-200 px-8 py-4 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center gap-2.5 no-underline">
            <div className="w-8 h-8 bg-blue-600 rounded-lg text-white text-sm font-bold flex items-center justify-center">
              &#8377;
            </div>
            <span className="text-xl font-bold text-blue-600">RazorFlow Ops</span>
          </Link>

          <div className="flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`px-4 py-2 rounded-lg text-sm font-medium no-underline transition-colors ${
                  location.pathname === link.path
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
            {demoMode ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-amber-50 border border-amber-200 rounded text-xs font-medium text-amber-700">
                <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                Demo Mode
              </span>
            ) : (
              <span className="text-sm text-gray-600">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            )}
          </div>
          <div className="h-6 w-px bg-gray-200" />
          <span className="text-sm text-gray-500">Merchant Portal</span>
        </div>
      </div>
    </nav>
  );
}
