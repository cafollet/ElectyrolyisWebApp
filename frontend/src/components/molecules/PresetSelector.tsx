/**
 * Component for selecting preset molecules.
 */

import { useQuery } from '@tanstack/react-query';
import { Beaker } from 'lucide-react';
import { Card, Spinner } from '../common';
import { apiClient } from '../../api/client';
import type { Molecule, PresetMolecule } from '../../types';

interface PresetSelectorProps {
  onSelect: (molecule: Molecule) => void;
}

export function PresetSelector({ onSelect }: PresetSelectorProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['presets'],
    queryFn: () => apiClient.getPresets(),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        Failed to load presets: {error.message}
      </div>
    );
  }

  const presets = data?.presets || {};

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Object.entries(presets).map(([key, preset]: [string, PresetMolecule]) => (
        <button
          key={key}
          onClick={() => onSelect(preset.molecule)}
          className="text-left p-4 bg-white border border-gray-200 rounded-lg hover:border-primary-500 hover:shadow-md transition-all group"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2">
              <Beaker className="w-5 h-5 text-quantum-600" />
              <h4 className="font-medium text-gray-900 group-hover:text-primary-700">
                {preset.name}
              </h4>
            </div>
            <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600">
              {preset.recommended_method.toUpperCase()}
            </span>
          </div>
          <p className="mt-2 text-sm text-gray-500">{preset.description}</p>
          <div className="mt-3 flex items-center justify-between text-xs text-gray-400">
            <span>{preset.molecule.atoms.length} atom(s)</span>
            <span>~{preset.expected_energy_hartree.toFixed(2)} Ha</span>
          </div>
        </button>
      ))}
    </div>
  );
}