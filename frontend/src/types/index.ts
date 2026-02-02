/**
 * Type definitions for the Quantum Chemistry Simulator.
 */

// Atom definition
export interface Atom {
  symbol: string;
  position: [number, number, number];
}

// Molecule definition
export interface Molecule {
  name: string;
  atoms: Atom[];
  charge: number;
  multiplicity: number;
  basis_set: string;
}

// VQE configuration
export interface VQEConfig {
  step_size: number;
  num_steps: number;
  convergence_threshold?: number;
}

// SQD configuration
export interface SQDConfig {
  samples_per_batch: number;
  max_iterations: number;
  num_batches: number;
  num_shots: number;
  use_hardware: boolean;
  ibm_api_key?: string;
}

// Simulation request
export interface SimulationRequest {
  molecule: Molecule;
  method: 'vqe' | 'sqd';
  vqe_config?: VQEConfig;
  sqd_config?: SQDConfig;
}

// Job status
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

// Job response
export interface Job {
  id: string;
  status: JobStatus;
  method: string;
  molecule_name: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  progress: number;
  current_step: string;
  result_energy?: number;
  energy_history?: number[];
  error_message?: string;
  result?: SimulationResult;
}

// Simulation result
export interface SimulationResult {
  energy_hartree: number;
  energy_ev: number;
  mapping?: string;
  converged: boolean;
  num_iterations: number;
  execution_time_seconds: number;
  metadata?: Record<string, unknown>;
}

// Preset molecule
export interface PresetMolecule {
  name: string;
  description: string;
  molecule: Molecule;
  expected_energy_hartree: number;
  recommended_method: 'vqe' | 'sqd';
}

// API response types
export interface CreateJobResponse {
  message: string;
  job_id: string;
  status: JobStatus;
  status_url: string;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface PresetsResponse {
  presets: Record<string, PresetMolecule>;
  count: number;
}

export interface ValidationResponse {
  valid: boolean;
  molecule_name: string;
  num_atoms: number;
  num_electrons: number;
  num_qubits_required: number;
  estimated_vqe_time_seconds?: number;
  estimated_sqd_time_seconds?: number;
  warnings: string[];
  recommended_method: 'vqe' | 'sqd';
}

// Element definition
export interface Element {
  symbol: string;
  name: string;
  atomic_number: number;
}