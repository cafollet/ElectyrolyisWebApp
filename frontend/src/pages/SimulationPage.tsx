/**
 * Main simulation page.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, AlertCircle } from 'lucide-react';
import { Button, Card } from '../components/common';
import { MoleculeBuilder } from '../components/molecules';
import { SimulationConfig, JobStatus } from '../components/simulation';
import { useSimulation, useValidation } from '../hooks';
import type { Molecule, VQEConfig, SQDConfig } from '../types';

const DEFAULT_MOLECULE: Molecule = {
  name: '',
  atoms: [{ symbol: 'H', position: [0, 0, -0.69] }, { symbol: 'H', position: [0, 0, 0.69] }],
  charge: 0,
  multiplicity: 1,
  basis_set: 'sto-3g',
};

const DEFAULT_VQE_CONFIG: VQEConfig = {
  step_size: 0.2,
  num_steps: 200,
};

const DEFAULT_SQD_CONFIG: SQDConfig = {
  samples_per_batch: 500,
  max_iterations: 100,
  num_batches: 5,
  num_shots: 10000,
  use_hardware: false,
};

export function SimulationPage() {
  const navigate = useNavigate();
  const { createSimulation, isCreating, createError, currentJobId, clearCurrentJob } = useSimulation();
  const { validate, isValidating, validationResult, validationError } = useValidation();

  const [molecule, setMolecule] = useState<Molecule>(DEFAULT_MOLECULE);
  const [method, setMethod] = useState<'vqe' | 'sqd'>('vqe');
  const [vqeConfig, setVqeConfig] = useState<VQEConfig>(DEFAULT_VQE_CONFIG);
  const [sqdConfig, setSqdConfig] = useState<SQDConfig>(DEFAULT_SQD_CONFIG);
  const [step, setStep] = useState<'build' | 'config' | 'running'>('build');

  const handleValidate = async () => {
    try {
      const result = await validate(molecule);
      if (result.valid) {
        setStep('config');
        // Auto-select recommended method
        if (result.recommended_method) {
          setMethod(result.recommended_method);
        }
      }
    } catch (err) {
      // Error handled by mutation
    }
  };

  const handleSubmit = async () => {
    try {
      clearCurrentJob();
      const response = await createSimulation({
        molecule,
        method,
        vqe_config: method === 'vqe' ? vqeConfig : undefined,
        sqd_config: method === 'sqd' ? sqdConfig : undefined,
      });
      setStep('running');
    } catch (err) {
      // Error handled by mutation
    }
  };

  const handleComplete = () => {
    if (currentJobId) {
      navigate(`/results?job=${currentJobId}`);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Progress Steps */}
      <div className="flex items-center justify-center space-x-4">
        {['build', 'config', 'running'].map((s, i) => (
          <div key={s} className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center font-medium ${
                step === s
                  ? 'bg-primary-600 text-white'
                  : i < ['build', 'config', 'running'].indexOf(step)
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-200 text-gray-600'
              }`}
            >
              {i + 1}
            </div>
            {i < 2 && <div className="w-16 h-1 bg-gray-200 mx-2" />}
          </div>
        ))}
      </div>

      {/* Step 1: Build Molecule */}
      {step === 'build' && (
        <>
          <MoleculeBuilder molecule={molecule} onChange={setMolecule} />

          {/* Validation Results */}
          {validationResult && (
            <Card>
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  {validationResult.valid ? (
                    <span className="text-green-600 font-medium">✓ Molecule is valid</span>
                  ) : (
                    <span className="text-red-600 font-medium">✗ Validation failed</span>
                  )}
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Electrons:</span>{' '}
                    <span className="font-medium">{validationResult.num_electrons}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Qubits:</span>{' '}
                    <span className="font-medium">{validationResult.num_qubits_required}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Recommended:</span>{' '}
                    <span className="font-medium">{validationResult.recommended_method?.toUpperCase()}</span>
                  </div>
                </div>
                {validationResult.warnings.length > 0 && (
                  <div className="flex items-start space-x-2 text-yellow-700 bg-yellow-50 p-3 rounded-lg">
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    <ul className="text-sm">
                      {validationResult.warnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Card>
          )}

          {validationError && (
            <Card>
              <div className="text-red-600 flex items-center space-x-2">
                <AlertCircle className="w-5 h-5" />
                <span>{validationError.message}</span>
              </div>
            </Card>
          )}

          <div className="flex justify-end">
            <Button onClick={handleValidate} loading={isValidating}>
              Validate & Continue
            </Button>
          </div>
        </>
      )}

      {/* Step 2: Configure Simulation */}
      {step === 'config' && (
        <>
          <SimulationConfig
            method={method}
            onMethodChange={setMethod}
            vqeConfig={vqeConfig}
            onVqeConfigChange={setVqeConfig}
            sqdConfig={sqdConfig}
            onSqdConfigChange={setSqdConfig}
          />

          {createError && (
            <Card>
              <div className="text-red-600 flex items-center space-x-2">
                <AlertCircle className="w-5 h-5" />
                <span>{createError.message}</span>
              </div>
            </Card>
          )}

          <div className="flex justify-between">
            <Button variant="secondary" onClick={() => setStep('build')}>
              Back
            </Button>
            <Button onClick={handleSubmit} loading={isCreating} variant="quantum">
              <Play className="w-4 h-4 mr-2" />
              Run Simulation
            </Button>
          </div>
        </>
      )}

      {/* Step 3: Running */}
      {step === 'running' && currentJobId && (
        <>
          <JobStatus jobId={currentJobId} onComplete={handleComplete} />

          <div className="flex justify-center">
            <Button variant="secondary" onClick={() => navigate('/results')}>
              View All Results
            </Button>
          </div>
        </>
      )}
    </div>
  );
}