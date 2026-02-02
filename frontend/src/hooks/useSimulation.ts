/**
 * Custom hook for managing simulations.
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { SimulationRequest, Job, ValidationResponse } from '../types';

export function useSimulation() {
  const queryClient = useQueryClient();
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  // Create simulation mutation
  const createMutation = useMutation({
    mutationFn: (request: SimulationRequest) => apiClient.createSimulation(request),
    onSuccess: (data) => {
      setCurrentJobId(data.job_id);
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  // Cancel simulation mutation
  const cancelMutation = useMutation({
    mutationFn: (jobId: string) => apiClient.cancelJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      if (currentJobId) {
        queryClient.invalidateQueries({ queryKey: ['job', currentJobId] });
      }
    },
  });

  // Get current job
  const currentJob = useQuery({
    queryKey: ['job', currentJobId],
    queryFn: () => apiClient.getJob(currentJobId!),
    enabled: !!currentJobId,
    refetchInterval: (query) => {
      const job = query.state.data;
      if (job?.status === 'completed' || job?.status === 'failed') {
        return false;
      }
      return 2000;
    },
  });

  // List all jobs
  const jobsList = useQuery({
    queryKey: ['jobs'],
    queryFn: () => apiClient.listJobs({ limit: 50 }),
  });

  return {
    // State
    currentJobId,
    currentJob: currentJob.data,
    isLoadingJob: currentJob.isLoading,
    jobs: jobsList.data?.jobs || [],
    isLoadingJobs: jobsList.isLoading,

    // Actions
    createSimulation: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    createError: createMutation.error,

    cancelSimulation: cancelMutation.mutateAsync,
    isCancelling: cancelMutation.isPending,

    setCurrentJobId,
    clearCurrentJob: () => setCurrentJobId(null),
  };
}

export function useValidation() {
  const [validationResult, setValidationResult] = useState<ValidationResponse | null>(null);

  const validateMutation = useMutation({
    mutationFn: apiClient.validateMolecule,
    onSuccess: setValidationResult,
  });

  return {
    validate: validateMutation.mutateAsync,
    isValidating: validateMutation.isPending,
    validationResult,
    validationError: validateMutation.error,
    clearValidation: () => setValidationResult(null),
  };
}