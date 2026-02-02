/**
 * Simulation configuration component.
 *
 * For VQE: step size, number of steps.
 * For SQD: batch / iteration / shot controls PLUS a two-mode toggle:
 *   • Simulate  – runs locally via Qiskit Aer (default)
 *   • IBM Quantum Hardware – user supplies an IBM Quantum API key;
 *     the backend forwards it to QiskitRuntimeService to connect to
 *     a real quantum processor.
 */

import { Card, Input } from '../common';
import type { VQEConfig, SQDConfig } from '../../types';

interface SimulationConfigProps {
  method: 'vqe' | 'sqd';
  onMethodChange: (method: 'vqe' | 'sqd') => void;
  vqeConfig: VQEConfig;
  onVqeConfigChange: (config: VQEConfig) => void;
  sqdConfig: SQDConfig;
  onSqdConfigChange: (config: SQDConfig) => void;
}

export function SimulationConfig({
  method,
  onMethodChange,
  vqeConfig,
  onVqeConfigChange,
  sqdConfig,
  onSqdConfigChange,
}: SimulationConfigProps) {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Simulation Settings</h2>

      {/* Method Selection */}
      <Card>
        <div className="space-y-4">
          <label className="label">Simulation Method</label>
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => onMethodChange('vqe')}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                method === 'vqe'
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <h4 className="font-medium text-gray-900">VQE</h4>
              <p className="text-sm text-gray-500 mt-1">
                Variational Quantum Eigensolver. Best for small molecules (≤16 qubits).
              </p>
            </button>

            <button
              onClick={() => onMethodChange('sqd')}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                method === 'sqd'
                  ? 'border-quantum-500 bg-quantum-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <h4 className="font-medium text-gray-900">SQD</h4>
              <p className="text-sm text-gray-500 mt-1">
                Sample-based Quantum Diagonalization. Handles larger molecules efficiently.
              </p>
            </button>
          </div>
        </div>
      </Card>

      {/* Method-specific Configuration */}
      {method === 'vqe' ? (
        <Card title="VQE Configuration">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Step Size"
              type="number"
              step="0.01"
              min="0.001"
              max="1"
              value={vqeConfig.step_size}
              onChange={(e) =>
                onVqeConfigChange({ ...vqeConfig, step_size: parseFloat(e.target.value) || 0.2 })
              }
              hint="Optimizer learning rate (0.001-1.0)"
            />

            <Input
              label="Number of Steps"
              type="number"
              min="10"
              max="5000"
              value={vqeConfig.num_steps}
              onChange={(e) =>
                onVqeConfigChange({ ...vqeConfig, num_steps: parseInt(e.target.value) || 200 })
              }
              hint="Maximum optimization iterations"
            />
          </div>
        </Card>
      ) : (
        <>
          {/* SQD: Backend selection (simulate vs real hardware) */}
          <Card title="Quantum Backend">
            <div className="space-y-3">
              <label className="label">Where to run the quantum circuit</label>
              <div className="grid grid-cols-2 gap-4">
                {/* Simulate option */}
                <button
                  onClick={() => onSqdConfigChange({ ...sqdConfig, use_hardware: false, ibm_api_key: '' })}
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    !sqdConfig.use_hardware
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <h4 className="font-medium text-gray-900">Simulate</h4>
                  <p className="text-sm text-gray-500 mt-1">
                    Runs locally via Qiskit Aer. No API key required.
                  </p>
                </button>

                {/* IBM Hardware option */}
                <button
                  onClick={() => onSqdConfigChange({ ...sqdConfig, use_hardware: true })}
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    sqdConfig.use_hardware
                      ? 'border-quantum-500 bg-quantum-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <h4 className="font-medium text-gray-900">IBM Quantum Hardware</h4>
                  <p className="text-sm text-gray-500 mt-1">
                    Connects to a real IBM quantum processor via your API key.
                  </p>
                </button>
              </div>

              {/* API key input — only visible when hardware mode is selected */}
              {sqdConfig.use_hardware && (
                <div className="mt-4">
                  <Input
                    label="IBM Quantum API Key"
                    type="password"
                    value={sqdConfig.ibm_api_key || ''}
                    onChange={(e) =>
                      onSqdConfigChange({ ...sqdConfig, ibm_api_key: e.target.value })
                    }
                    placeholder="paste your IBM Quantum API key here"
                    hint="Obtain from https://quantum.ibm.com. The key is sent to the backend at job submission and is not persisted."
                  />
                  {sqdConfig.use_hardware && !sqdConfig.ibm_api_key && (
                    <p className="text-sm text-red-600 mt-1">
                      An API key is required to use IBM Quantum hardware.
                    </p>
                  )}
                </div>
              )}
            </div>
          </Card>

          {/* SQD sampling / iteration parameters */}
          <Card title="SQD Configuration">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Samples per Batch"
                type="number"
                min="50"
                max="10000"
                value={sqdConfig.samples_per_batch}
                onChange={(e) =>
                  onSqdConfigChange({
                    ...sqdConfig,
                    samples_per_batch: parseInt(e.target.value) || 500,
                  })
                }
                hint="Number of samples in each batch"
              />

              <Input
                label="Max Iterations"
                type="number"
                min="5"
                max="500"
                value={sqdConfig.max_iterations}
                onChange={(e) =>
                  onSqdConfigChange({
                    ...sqdConfig,
                    max_iterations: parseInt(e.target.value) || 100,
                  })
                }
                hint="Maximum SQD iterations"
              />

              <Input
                label="Number of Batches"
                type="number"
                min="1"
                max="20"
                value={sqdConfig.num_batches}
                onChange={(e) =>
                  onSqdConfigChange({
                    ...sqdConfig,
                    num_batches: parseInt(e.target.value) || 5,
                  })
                }
                hint="Parallel batches for eigenstate solving"
              />

              <Input
                label="Quantum Shots"
                type="number"
                min="1000"
                max="100000"
                step="1000"
                value={sqdConfig.num_shots}
                onChange={(e) =>
                  onSqdConfigChange({
                    ...sqdConfig,
                    num_shots: parseInt(e.target.value) || 10000,
                  })
                }
                hint="Number of circuit measurements"
              />
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
