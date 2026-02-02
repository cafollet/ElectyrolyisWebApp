/**
 * Application header component.
 */

import { Link, useLocation } from 'react-router-dom';
import { Atom, FlaskConical, History } from 'lucide-react';
import clsx from 'clsx';

export function Header() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Home', icon: Atom },
    { path: '/simulate', label: 'Simulate', icon: FlaskConical },
    { path: '/results', label: 'Results', icon: History },
  ];

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-gradient-to-br from-quantum-500 to-primary-600 rounded-lg flex items-center justify-center">
              <Atom className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">QuantumChem</span>
          </Link>

          {/* Navigation */}
          <nav className="flex space-x-1">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={clsx(
                  'flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  location.pathname === path
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                )}
              >
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}