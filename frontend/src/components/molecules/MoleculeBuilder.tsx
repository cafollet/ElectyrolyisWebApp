/**
 * Main molecule builder component.
 *
 * Layout order:
 *   1. Molecule name
 *   2. Basis set selector  ← must come before atoms so the dropdown is already filtered
 *   3. Atoms (each AtomInput receives the current basisSet)
 *   4. Charge / Multiplicity
 *
 * A yellow banner is shown at the top of the Atoms card whenever one or more
 * atoms are invalid for the currently selected basis set.
 */

import { useState } from 'react';
import { Plus, Wand2 } from 'lucide-react';
import { Card, Button, Input, Select } from '../common';
import { AtomInput } from './AtomInput';
import { PresetSelector } from './PresetSelector';
import { isElementSupported } from '../../utils/elements';
import type { Molecule, Atom } from '../../types';

const BASIS_SETS = [
  { value: 'sto-3g', label: 'STO-3G (Minimal)' },
  { value: 'dyall-ae4z', label: 'dyall-AE4Z (Production)' },
  { value: 'sto-6g', label: 'STO-6G' },
  { value: '3-21g', label: '3-21G' },
  { value: '6-31g', label: '6-31G' },
  { value: '6-31g*', label: '6-31G*' },
  { value: 'cc-pvdz', label: 'cc-pVDZ' },
  { value: 'cc-pvtz', label: 'cc-pVTZ' },
  { value: 'def2-svp', label: 'def2-SVP (Production Alternate 1)' },
  { value: 'def2-tzvp', label: 'def2-TZVP (Production Alternate 2)' },
];

const DEFAULT_ATOM: Atom = { symbol: 'H', position: [0, 0, 0] };

interface MoleculeBuilderProps {
  molecule: Molecule;
  onChange: (molecule: Molecule) => void;
}

export function MoleculeBuilder({ molecule, onChange }: MoleculeBuilderProps) {
  const [showPresets, setShowPresets] = useState(false);

  // Collect symbols that are invalid for the current basis set
  const invalidAtoms = molecule.atoms.filter(
    (atom) => !isElementSupported(atom.symbol, molecule.basis_set)
  );

  const handleAtomChange = (index: number, atom: Atom) => {
    const newAtoms = [...molecule.atoms];
    newAtoms[index] = atom;
    onChange({ ...molecule, atoms: newAtoms });
  };

  const handleAddAtom = () => {
    onChange({ ...molecule, atoms: [...molecule.atoms, { ...DEFAULT_ATOM }] });
  };

  const handleRemoveAtom = (index: number) => {
    const newAtoms = molecule.atoms.filter((_, i) => i !== index);
    onChange({ ...molecule, atoms: newAtoms });
  };

  const handlePresetSelect = (preset: Molecule) => {
    onChange(preset);
    setShowPresets(false);
  };

  return (
    <div className="space-y-6">
      {/* Preset Toggle */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-900">Define Molecule</h2>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setShowPresets(!showPresets)}
        >
          <Wand2 className="w-4 h-4 mr-2" />
          {showPresets ? 'Manual Input' : 'Use Preset'}
        </Button>
      </div>

      {showPresets ? (
        <Card title="Select a Preset Molecule">
          <PresetSelector onSelect={handlePresetSelect} />
        </Card>
      ) : (
        <>
          {/* Molecule Name */}
          <Card>
            <Input
              label="Molecule Name"
              value={molecule.name}
              onChange={(e) => onChange({ ...molecule, name: e.target.value })}
              placeholder="e.g., Hydrogen, Water, Benzene"
              hint="Optional: Give your molecule a descriptive name"
            />
          </Card>

          {/* Basis Set — placed BEFORE atoms so the element dropdown is already filtered */}
          <Card title="Basis Set">
            <Select
              label="Basis Set"
              value={molecule.basis_set}
              onChange={(e) => onChange({ ...molecule, basis_set: e.target.value })}
              options={BASIS_SETS}
            />
            <p className="text-sm text-gray-500 mt-2">
              The selected basis set determines which elements are available in the atom picker below.
            </p>
          </Card>

          {/* Atoms */}
          <Card title="Atoms" subtitle="Add atoms and specify their 3D coordinates in Angstroms">
            {/* Banner when one or more atoms became invalid after a basis-set change */}
            {invalidAtoms.length > 0 && (
              <div className="mb-4 p-3 bg-yellow-50 border border-yellow-300 rounded-lg">
                <p className="text-sm text-yellow-800">
                  ⚠ The following atoms are not supported by{' '}
                  <strong>{molecule.basis_set}</strong>:{' '}
                  <strong>
                    {[...new Set(invalidAtoms.map((a) => a.symbol))].join(', ')}
                  </strong>
                  . Please update them or choose a different basis set.
                </p>
              </div>
            )}

            <div className="space-y-3">
              {molecule.atoms.map((atom, index) => (
                <AtomInput
                  key={index}
                  atom={atom}
                  index={index}
                  basisSet={molecule.basis_set}
                  onChange={handleAtomChange}
                  onRemove={handleRemoveAtom}
                  canRemove={molecule.atoms.length > 1}
                />
              ))}
            </div>

            <Button
              variant="secondary"
              size="sm"
              onClick={handleAddAtom}
              className="mt-4"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Atom
            </Button>
          </Card>

          {/* Charge & Multiplicity */}
          <Card title="Molecular Properties">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Charge"
                type="number"
                value={molecule.charge}
                onChange={(e) => onChange({ ...molecule, charge: parseInt(e.target.value) || 0 })}
                hint="Total molecular charge"
              />

              <Input
                label="Multiplicity"
                type="number"
                min={1}
                value={molecule.multiplicity}
                onChange={(e) => onChange({ ...molecule, multiplicity: parseInt(e.target.value) || 1 })}
                hint="Spin multiplicity (2S+1)"
              />
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
