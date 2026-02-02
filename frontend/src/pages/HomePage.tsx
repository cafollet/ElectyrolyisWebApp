/**
 * Home page component.
 */

import { Link } from 'react-router-dom';
import { Atom, Zap, Cpu, ArrowRight } from 'lucide-react';
import { Button, Card } from '../components/common';

export function HomePage() {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-12">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-quantum-500 to-primary-600 rounded-2xl mb-6">
          <Atom className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Quantum Chemistry Simulator
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
          Compute molecular ground state energies using cutting-edge quantum algorithms.
          Powered by VQE and SQD methods.
        </p>
        <div className="flex justify-center space-x-4">
          <Link to="/simulate">
            <Button size="lg">
              Start Simulation
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
          <Link to="/results">
            <Button variant="secondary" size="lg">
              View Past Results
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="grid md:grid-cols-3 gap-6">
        <Card>
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-primary-100 rounded-xl mb-4">
              <Atom className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Molecular Builder
            </h3>
            <p className="text-gray-600">
              Define custom molecules or choose from our preset library of common chemical systems.
            </p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-quantum-100 rounded-xl mb-4">
              <Cpu className="w-6 h-6 text-quantum-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Quantum Algorithms
            </h3>
            <p className="text-gray-600">
              Choose between VQE for small molecules or SQD for larger systems with optimal mappings.
            </p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-green-100 rounded-xl mb-4">
              <Zap className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Real-time Results
            </h3>
            <p className="text-gray-600">
              Track simulation progress and view energy convergence charts in real-time.
            </p>
          </div>
        </Card>
      </section>

      {/* Quick Start */}
      <section>
        <Card title="Quick Start Guide">
          <ol className="space-y-4">
            <li className="flex items-start">
              <span className="flex items-center justify-center w-8 h-8 bg-primary-100 text-primary-700 rounded-full font-semibold mr-3 flex-shrink-0">
                1
              </span>
              <div>
                <h4 className="font-medium text-gray-900">Define Your Molecule</h4>
                <p className="text-gray-600">
                  Add atoms with their 3D coordinates, or select a preset molecule.
                </p>
              </div>
            </li>
            <li className="flex items-start">
              <span className="flex items-center justify-center w-8 h-8 bg-primary-100 text-primary-700 rounded-full font-semibold mr-3 flex-shrink-0">
                2
              </span>
              <div>
                <h4 className="font-medium text-gray-900">Choose Algorithm</h4>
                <p className="text-gray-600">
                  Select VQE for small molecules or SQD for larger systems.
                </p>
              </div>
            </li>
            <li className="flex items-start">
              <span className="flex items-center justify-center w-8 h-8 bg-primary-100 text-primary-700 rounded-full font-semibold mr-3 flex-shrink-0">
                3
              </span>
              <div>
                <h4 className="font-medium text-gray-900">Run & Analyze</h4>
                <p className="text-gray-600">
                  Submit your simulation and watch the energy converge to the ground state.
                </p>
              </div>
            </li>
          </ol>
        </Card>
      </section>
    </div>
  );
}