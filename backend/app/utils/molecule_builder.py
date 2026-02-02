"""
Molecule building utilities.

Converts API molecule definitions to quantum chemistry objects.
"""

from typing import Dict, Any, Union, List, Set
import numpy as np

import pennylane as qml
from pennylane import qchem
import pyscf


# ---------------------------------------------------------------------------
# Full periodic table: symbol → atomic number (Z 1–118)
# ---------------------------------------------------------------------------
ATOMIC_NUMBERS: Dict[str, int] = {
    'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8,
    'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15,
    'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22,
    'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29,
    'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36,
    'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42, 'Tc': 43,
    'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50,
    'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57,
    'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64,
    'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71,
    'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78,
    'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85,
    'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90, 'Pa': 91, 'U': 92,
    'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99,
    'Fm': 100, 'Md': 101, 'No': 102, 'Lr': 103, 'Rf': 104, 'Db': 105,
    'Sg': 106, 'Bh': 107, 'Hs': 108, 'Mt': 109, 'Ds': 110, 'Rg': 111,
    'Cn': 112, 'Nh': 113, 'Fl': 114, 'Mc': 115, 'Lv': 116, 'Ts': 117,
    'Og': 118,
}


# Basis-set element ranges — verified against basissetexchange.org
# Each value is a list of inclusive (lo, hi) tuples of atomic numbers.

_BASIS_Z_RANGES: Dict[str, List[tuple]] = {
    'sto-3g':     [(1, 54)],                  # H – Xe
    'sto-6g':     [(1, 54)],                  # H – Xe
    '3-21g':      [(1, 55)],                  # H – Cs
    '6-31g':      [(1, 36)],                  # H – Kr
    '6-31g*':     [(1, 36)],                  # H – Kr
    '6-31g**':    [(1, 36)],                  # H – Kr  (same coverage as 6-31g*)
    'cc-pvdz':    [(1, 18), (20, 36)],        # H – Kr, K (19) missing
    'cc-pvtz':    [(1, 18), (20, 36)],        # H – Kr, K (19) missing
    'def2-svp':   [(1, 86)],                  # H – Rn
    'def2-tzvp':  [(1, 86)],                  # H – Rn
    'dyall-ae4z': [(1, 118)],                 # all elements
}


def _supported_z_set(basis_set: str) -> Set[int]:
    """Return the set of atomic numbers supported by *basis_set*."""
    ranges = _BASIS_Z_RANGES.get(basis_set.lower())
    if ranges is None:
        # Unknown basis set → allow everything (PySCF will error if truly unsupported)
        return set(range(1, 119))
    s: Set[int] = set()
    for lo, hi in ranges:
        s.update(range(lo, hi + 1))
    return s


class MoleculeBuilder:
    """
    Builds molecule objects from API definitions.

    Supports creating both PennyLane and PySCF molecules
    based on the simulation method requirements.
    """

    def build(
            self,
            molecule_data: Dict[str, Any],
            for_sqd: bool = False
    ) -> Union[qchem.Molecule, pyscf.gto.Mole]:
        """
        Build a molecule object from API data.

        Args:
            molecule_data: Dictionary with atoms, charge, multiplicity, basis_set.
            for_sqd: If True, builds PySCF molecule for SQD.

        Returns:
            PennyLane Molecule or PySCF Mole object.
        """
        atoms = molecule_data['atoms']
        charge = molecule_data.get('charge', 0)
        multiplicity = molecule_data.get('multiplicity', 1)
        basis_set = molecule_data.get('basis_set', 'sto-3g')

        symbols = [atom['symbol'] for atom in atoms]
        positions = np.array([atom['position'] for atom in atoms])

        if for_sqd:
            return self._build_pyscf(symbols, positions, charge, multiplicity, basis_set)
        else:
            return self._build_pennylane(symbols, positions, charge, multiplicity, basis_set)

    def _build_pennylane(
            self,
            symbols: List[str],
            positions: np.ndarray,
            charge: int,
            multiplicity: int,
            basis_set: str
    ) -> qchem.Molecule:
        """Build PennyLane molecule."""
        from jax import numpy as jnp

        return qchem.Molecule(
            symbols=symbols,
            coordinates=jnp.array(positions),
            charge=charge,
            mult=multiplicity,
            basis_name=basis_set
        )

    def _build_pyscf(
            self,
            symbols: List[str],
            positions: np.ndarray,
            charge: int,
            multiplicity: int,
            basis_set: str
    ) -> pyscf.gto.Mole:
        """Build PySCF molecule."""
        mol = pyscf.gto.Mole()

        atom_list = [
            [symbols[i], tuple(positions[i])]
            for i in range(len(symbols))
        ]

        spin = multiplicity - 1

        mol.build(
            atom=atom_list,
            basis=basis_set,
            charge=charge,
            spin=spin
        )

        return mol

    def validate(self, molecule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate molecule definition and compute properties.

        Checks include:
        - Unknown element symbols
        - Multiplicity / electron-count parity
        - Each atom's element is supported by the chosen basis set

        Args:
            molecule_data: Molecule definition from API.

        Returns:
            Dictionary with validation results and computed properties.
        """
        atoms = molecule_data['atoms']
        charge = molecule_data.get('charge', 0)
        multiplicity = molecule_data.get('multiplicity', 1)
        basis_set = molecule_data.get('basis_set', 'sto-3g')

        warnings: List[str] = []

        # Count electrons
        num_electrons = sum(
            ATOMIC_NUMBERS.get(atom['symbol'], 0)
            for atom in atoms
        ) - charge

        # Estimate qubit count (simplified)
        num_qubits = num_electrons * 2

        # --- Unknown elements ---
        for atom in atoms:
            if atom['symbol'] not in ATOMIC_NUMBERS:
                warnings.append(f"Unknown element: {atom['symbol']}")

        # --- Basis-set element support ---
        allowed = _supported_z_set(basis_set)
        for atom in atoms:
            z = ATOMIC_NUMBERS.get(atom['symbol'])
            if z is not None and z not in allowed:
                warnings.append(
                    f"Element {atom['symbol']} (Z={z}) is not supported by basis set '{basis_set}'"
                )

        # --- Multiplicity check ---
        if (num_electrons + multiplicity) % 2 != 1:
            warnings.append(
                f"Multiplicity {multiplicity} may be invalid for {num_electrons} electrons"
            )

        # Recommend method based on size
        if num_qubits <= 16:
            recommended_method = 'vqe'
            estimated_vqe_time = num_qubits * 10
            estimated_sqd_time = num_qubits * 5
        else:
            recommended_method = 'sqd'
            estimated_vqe_time = None
            estimated_sqd_time = num_qubits * 5

        return {
            'valid': len(warnings) == 0 or all('Unknown' not in w for w in warnings),
            'num_electrons': num_electrons,
            'num_qubits': num_qubits,
            'warnings': warnings,
            'recommended_method': recommended_method,
            'estimated_vqe_time': estimated_vqe_time,
            'estimated_sqd_time': estimated_sqd_time
        }
