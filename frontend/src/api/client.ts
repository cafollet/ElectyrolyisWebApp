/**
 * API client for communicating with the backend.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  SimulationRequest,
  CreateJobResponse,
  Job,
  JobListResponse,
  PresetsResponse,
  ValidationResponse,
  Molecule,
  Element,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

// Create axios instance
const client: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ error?: string }>) => {
    const message = error.response?.data?.error || error.message || 'An error occurred';
    return Promise.reject(new Error(message));
  }
);

// API functions (not a class to avoid `this` binding issues)
export const apiClient = {
  // Simulation endpoints
  createSimulation: async (request: SimulationRequest): Promise<CreateJobResponse> => {
    const response = await client.post<CreateJobResponse>('/simulations', request);
    return response.data;
  },

  getJob: async (jobId: string): Promise<Job> => {
    const response = await client.get<Job>(`/simulations/${jobId}`);
    return response.data;
  },

  listJobs: async (params?: { status?: string; limit?: number; offset?: number }): Promise<JobListResponse> => {
    const response = await client.get<JobListResponse>('/simulations', { params });
    return response.data;
  },

  cancelJob: async (jobId: string): Promise<void> => {
    await client.delete(`/simulations/${jobId}`);
  },

  getEnergyHistory: async (jobId: string): Promise<{ energy_history: number[]; final_energy: number }> => {
    const response = await client.get(`/simulations/${jobId}/energy-history`);
    return response.data;
  },

  // Molecule endpoints
  getPresets: async (): Promise<PresetsResponse> => {
    const response = await client.get<PresetsResponse>('/molecules/presets');
    return response.data;
  },

  validateMolecule: async (molecule: Molecule): Promise<ValidationResponse> => {
    const response = await client.post<ValidationResponse>('/molecules/validate', molecule);
    return response.data;
  },

  getElements: async (): Promise<{ elements: Element[] }> => {
    const response = await client.get('/molecules/elements');
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<{ status: string }> => {
    const response = await client.get('/health', { baseURL: '' });
    return response.data;
  },
};

export default apiClient;