/**
 * Component for inputting a single atom's details.
 *
 * The element dropdown is filtered in real-time to only show elements
 * supported by the currently selected basis set. If the atom's current
 * symbol is not in that set (e.g. after a basis-set switch) an inline
 * red warning is rendered below the select.
 */

import { Trash2 } from 'lucide-react';
import { Input, Select, Button } from '../common';
import { getElementsForBasisSet, isElementSupported } from '../../utils/elements';
import type { Atom } from '../../types';

interface AtomInputProps {
  atom: Atom;
  index: number;
  basisSet: string;
  onChange: (index: number, atom: Atom) => void;
  onRemove: (index: number) => void;
  canRemove: boolean;
}

export function AtomInput({ atom, index, basisSet, onChange, onRemove, canRemove }: AtomInputProps) {
  // Build dropdown options from the basis-set filter
  const supportedElements = getElementsForBasisSet(basisSet);
  const elementOptions = supportedElements.map((el) => ({
    value: el.symbol,
    label: `${el.symbol} - ${el.name}`,
  }));

  // Is the current symbol valid for this basis set?
  const symbolValid = isElementSupported(atom.symbol, basisSet);

  const handleSymbolChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange(index, { ...atom, symbol: e.target.value });
  };

  const handlePositionChange = (axis: 0 | 1 | 2, value: string) => {
    const newPosition: [number, number, number] = [...atom.position];
    newPosition[axis] = parseFloat(value) || 0;
    onChange(index, { ...atom, position: newPosition });
  };

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-end gap-3 p-3 bg-gray-50 rounded-lg">
        {/* Element selector */}
        <div className="w-44">
          <Select
            label={index === 0 ? 'Element' : undefined}
            value={symbolValid ? atom.symbol : ''}
            onChange={handleSymbolChange}
            options={elementOptions}
          />
        </div>

        {/* XYZ coordinates */}
        <div className="flex-1 grid grid-cols-3 gap-2">
          <Input
            label={index === 0 ? 'X (Å)' : undefined}
            type="number"
            step="0.01"
            value={atom.position[0]}
            onChange={(e) => handlePositionChange(0, e.target.value)}
            placeholder="X"
          />
          <Input
            label={index === 0 ? 'Y (Å)' : undefined}
            type="number"
            step="0.01"
            value={atom.position[1]}
            onChange={(e) => handlePositionChange(1, e.target.value)}
            placeholder="Y"
          />
          <Input
            label={index === 0 ? 'Z (Å)' : undefined}
            type="number"
            step="0.01"
            value={atom.position[2]}
            onChange={(e) => handlePositionChange(2, e.target.value)}
            placeholder="Z"
          />
        </div>

        {/* Remove button */}
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onRemove(index)}
          disabled={!canRemove}
          className="text-red-600 hover:text-red-700 hover:bg-red-50"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>

      {/* Inline warning when the atom is unsupported by the current basis set */}
      {!symbolValid && (
        <p className="text-sm text-red-600 pl-3">
          ⚠ <strong>{atom.symbol}</strong> is not supported by <strong>{basisSet}</strong>.
          Please change this atom or select a different basis set.
        </p>
      )}
    </div>
  );
}
