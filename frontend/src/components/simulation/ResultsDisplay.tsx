/**
 * Full results display component.
 */

import { Zap, Clock, Cpu, GitBranch } from 'lucide-react';
import { Card } from '../common';
import { EnergyChart } from './EnergyChart';
import { formatEnergy, formatDuration } from '../../utils/format';
import type { Job } from '../../types';

interface ResultsDisplayProps {
  job: Job;
}

export function ResultsDisplay({ job }: ResultsDisplayProps) {
  const result = job.result;

  return (
    <div className="space-y-6">
      {/* Main Energy Result */}
      <Card>
        <div className="text-center py-6">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
            <Zap className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Ground State Energy</h2>
          <div className="space-y-1">
            <p className="text-4xl font-mono font-bold text-primary-600">
              {formatEnergy(job.result_energy || 0)}
            </p>
            <p className="text-lg text-gray-500">
              {formatEnergy(job.result_energy || 0, 'ev')}
            </p>
          </div>
        </div>
      </Card>

      {/* Energy Convergence Chart */}
      {job.energy_history && job.energy_history.length > 0 && (
        <EnergyChart
          energyHistory={job.energy_history}
          finalEnergy={job.result_energy}
        />
      )}

      {/* Detailed Results */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Cpu className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Method</p>
              <p className="font-semibold text-gray-900">{job.method.toUpperCase()}</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <GitBranch className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Mapping</p>
              <p className="font-semibold text-gray-900">
                {result?.mapping || 'Jordan-Wigner'}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Clock className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Execution Time</p>
              <p className="font-semibold text-gray-900">
                {result?.execution_time_seconds
                  ? formatDuration(result.execution_time_seconds)
                  : 'N/A'}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Zap className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Iterations</p>
              <p className="font-semibold text-gray-900">
                {result?.num_iterations || job.energy_history?.length || 0}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Convergence Status */}
      {result && (
        <Card title="Convergence Status">
          <div className="flex items-center space-x-2">
            <div
              className={`w-3 h-3 rounded-full ${
                result.converged ? 'bg-green-500' : 'bg-yellow-500'
              }`}
            />
            <span className="text-gray-700">
              {result.converged
                ? 'Simulation converged successfully'
                : 'Simulation completed (convergence not confirmed)'}
            </span>
          </div>
        </Card>
      )}
    </div>
  );
}