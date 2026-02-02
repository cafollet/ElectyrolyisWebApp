/**
 * Results page for viewing simulation history.
 */

import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Clock, ChevronRight } from 'lucide-react';
import { Card, Spinner } from '../components/common';
import { ResultsDisplay } from '../components/simulation';
import { useSimulation } from '../hooks';
import { formatDate, formatStatus, getStatusColor, formatEnergy } from '../utils/format';
import type { Job } from '../types';

export function ResultsPage() {
  const [searchParams] = useSearchParams();
  const jobIdParam = searchParams.get('job');

  const { jobs, isLoadingJobs, setCurrentJobId, currentJob, isLoadingJob } = useSimulation();
  const [selectedJobId, setSelectedJobId] = useState<string | null>(jobIdParam);

  useEffect(() => {
    if (jobIdParam) {
      setSelectedJobId(jobIdParam);
      setCurrentJobId(jobIdParam);
    }
  }, [jobIdParam, setCurrentJobId]);

  const handleSelectJob = (jobId: string) => {
    setSelectedJobId(jobId);
    setCurrentJobId(jobId);
  };

  if (isLoadingJobs) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Job List */}
      <div className="lg:col-span-1 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Simulation History</h2>

        {jobs.length === 0 ? (
          <Card>
            <div className="text-center py-8 text-gray-500">
              <Clock className="w-12 h-12 mx-auto mb-3 text-gray-300"  />
              <p>No simulations yet</p>
              <p className="text-sm">Run your first simulation to see results here</p>
            </div>
          </Card>
        ) : (
          <div className="space-y-2">
            {jobs.map((job) => (
              <button
                key={job.id}
                onClick={() => handleSelectJob(job.id)}
                className={`w-full text-left p-4 rounded-lg border transition-all ${
                  selectedJobId === job.id
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-gray-900 truncate">
                      {job.molecule_name || `Job ${job.id.slice(0, 8)}`}
                    </h4>
                    <div className="flex items-center space-x-2 mt-1">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(job.status)}`}
                      >
                        {formatStatus(job.status)}
                      </span>
                      <span className="text-xs text-gray-500">{job.method.toUpperCase()}</span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">{formatDate(job.created_at)}</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>

                {job.status === 'completed' && job.result_energy && (
                  <div className="mt-2 pt-2 border-t border-gray-100">
                    <span className="text-sm font-mono text-green-600">
                      {formatEnergy(job.result_energy)}
                    </span>
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Selected Job Details */}
      <div className="lg:col-span-2">
        {selectedJobId ? (
          isLoadingJob ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : currentJob ? (
            currentJob.status === 'completed' ? (
              <ResultsDisplay job={currentJob} />
            ) : (
              <Card>
                <div className="text-center py-8">
                  <div
                    className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                      currentJob.status
                    )}`}
                  >
                    {formatStatus(currentJob.status)}
                  </div>
                  <h3 className="mt-4 text-lg font-medium text-gray-900">
                    {currentJob.molecule_name || 'Simulation'}
                  </h3>
                  {currentJob.status === 'running' && (
                    <div className="mt-4">
                      <div className="w-full bg-gray-200 rounded-full h-2 max-w-xs mx-auto">
                        <div
                          className="bg-primary-600 h-2 rounded-full transition-all"
                          style={{ width: `${currentJob.progress}%` }}
                        />
                      </div>
                      <p className="text-sm text-gray-500 mt-2">{currentJob.current_step}</p>
                    </div>
                  )}
                  {currentJob.error_message && (
                    <p className="mt-4 text-red-600 text-sm">{currentJob.error_message}</p>
                  )}
                </div>
              </Card>
            )
          ) : (
            <Card>
              <div className="text-center py-8 text-gray-500">Job not found</div>
            </Card>
          )
        ) : (
          <Card>
            <div className="text-center py-12 text-gray-500">
              <p>Select a simulation from the list to view details</p>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}