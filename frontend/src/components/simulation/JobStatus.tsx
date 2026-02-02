/**
 * Job status display component.
 */

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { Card, Spinner } from '../common';
import { apiClient } from '../../api/client';
import { formatStatus, getStatusColor, formatDuration, formatDate } from '../../utils/format';
import type { Job } from '../../types';

interface JobStatusProps {
  jobId: string;
  onComplete?: (job: Job) => void;
}

export function JobStatus({ jobId, onComplete }: JobStatusProps) {
  const { data: job, isLoading, error } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => apiClient.getJob(jobId),
    refetchInterval: (query) => {
      const job = query.state.data;
      // Stop polling when job is complete or failed
      if (job?.status === 'completed' || job?.status === 'failed' || job?.status === 'cancelled') {
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
  });

  useEffect(() => {
    if (job?.status === 'completed' && onComplete) {
      onComplete(job);
    }
  }, [job?.status, job, onComplete]);

  if (isLoading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <Spinner />
          <span className="ml-3 text-gray-500">Loading job status...</span>
        </div>
      </Card>
    );
  }

  if (error || !job) {
    return (
      <Card>
        <div className="text-center py-8 text-red-600">
          <XCircle className="w-12 h-12 mx-auto mb-3" />
          <p>Failed to load job status</p>
          <p className="text-sm text-gray-500 mt-1">{error?.message}</p>
        </div>
      </Card>
    );
  }

  const StatusIcon = {
    pending: Clock,
    running: Loader2,
    completed: CheckCircle,
    failed: XCircle,
    cancelled: XCircle,
  }[job.status] || Clock;

  return (
    <Card>
      <div className="space-y-4">
        {/* Status Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <StatusIcon
              className={`w-6 h-6 ${
                job.status === 'running' ? 'animate-spin text-blue-600' : ''
              } ${job.status === 'completed' ? 'text-green-600' : ''} ${
                job.status === 'failed' ? 'text-red-600' : ''
              }`}
            />
            <div>
              <h3 className="font-medium text-gray-900">
                {job.molecule_name || 'Simulation'}
              </h3>
              <span
                className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${getStatusColor(
                  job.status
                )}`}
              >
                {formatStatus(job.status)}
              </span>
            </div>
          </div>
          <span className="text-sm text-gray-500">{job.method.toUpperCase()}</span>
        </div>

        {/* Progress Bar */}
        {(job.status === 'running' || job.status === 'pending') && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">{job.current_step || 'Initializing...'}</span>
              <span className="text-gray-700 font-medium">{job.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${job.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Timestamps */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Created:</span>
            <p className="text-gray-900">{formatDate(job.created_at)}</p>
          </div>
          {job.completed_at && (
            <div>
              <span className="text-gray-500">Completed:</span>
              <p className="text-gray-900">{formatDate(job.completed_at)}</p>
            </div>
          )}
        </div>

        {/* Error Message */}
        {job.error_message && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">{job.error_message}</p>
          </div>
        )}

        {/* Quick Result Preview */}
        {job.status === 'completed' && job.result_energy && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-700">
              Ground State Energy: <strong>{job.result_energy.toFixed(6)} Ha</strong>
            </p>
          </div>
        )}
      </div>
    </Card>
  );
}