"""
Molecule representation and handling.

This module provides a unified interface for working with molecular
systems from both PennyLane and PySCF.
"""

from dataclasses import dataclass, field
from typing import Union, Optional, List, Tuple
import numpy as np

import pennylane as qml
from pennylane import qchem
import pyscf
from pyscf import gto

from .config import FermionMapping, QubitDevice
from .mappings import select_optimal_mapping
from .exceptions import MoleculeConfigurationError

MoleculeInput = Union[qchem.Molecule, pyscf.gto.Mole]


@dataclass
class MoleculeProperties:
    """
    Computed molecular properties.

    Attributes:
        n_electrons: Total number of electrons.
        n_qubits: Number of qubits required for simulation.
        n_orbitals: Number of molecular orbitals.
        spin: Spin multiplicity.
        charge: Molecular charge.
        is_open_shell: Whether the system is open-shell.
    """
    n_electrons: int
    n_qubits: int
    n_orbitals: int
    spin: int = 0
    charge: int = 0
    is_open_shell: bool = False


class MoleculeWrapper:
    """
    Unified wrapper for molecular systems.

    Provides a consistent interface for molecules defined using either
    PennyLane's qchem.Molecule or PySCF's gto.Mole.

    Attributes:
        name: Human-readable name for the molecule.
        properties: Computed molecular properties.
        qubit_hamiltonian: The qubit Hamiltonian for simulation.
        mapping: The fermion-to-qubit mapping used.

    Example:
        >>> symbols = ['H', 'H']
        >>> coords = np.array([[0, 0, -0.7], [0, 0, 0.7]])
        >>> mol = qchem.Molecule(symbols, coords)
        >>> wrapper = MoleculeWrapper(mol, name="Hydrogen")
        >>> print(wrapper.properties.n_electrons)
        2
    """

    def __init__(
            self,
            molecule: MoleculeInput,
            name: str = "",
            device: QubitDevice = QubitDevice.DEFAULT_QUBIT
    ):
        """
        Initialize molecule wrapper.

        Args:
            molecule: PennyLane Molecule or PySCF Mole object.
            name: Optional name for the molecule.
            device: Quantum device for simulation.

        Raises:
            MoleculeConfigurationError: If molecule configuration is invalid.
        """
        self.name = name
        self._raw_molecule = molecule
        self._device_type = device

        self._pyscf_mol: Optional[pyscf.gto.Mole] = None
        self._fermionic_hamiltonian = None
        self.qubit_hamiltonian = None
        self.mapping: Optional[FermionMapping] = None
        self.properties: Optional[MoleculeProperties] = None

        self._initialize()

    def _initialize(self) -> None:
        """Initialize molecular properties and Hamiltonians."""
        if isinstance(self._raw_molecule, qchem.Molecule):
            self._init_from_pennylane()
        elif isinstance(self._raw_molecule, pyscf.gto.Mole):
            self._init_from_pyscf()
        else:
            raise MoleculeConfigurationError(
                f"Unsupported molecule type: {type(self._raw_molecule)}"
            )

    def _init_from_pennylane(self) -> None:
        """Initialize from PennyLane molecule."""
        mol = self._raw_molecule

        # Build PySCF molecule for compatibility
        self._pyscf_mol = pyscf.gto.Mole()
        self._pyscf_mol.build(
            atom=[
                [mol.symbols[i], mol.coordinates[i]]
                for i in range(len(mol.symbols))
            ],
            basis=mol.basis_name,
            spin=int((mol.mult - 1) / 2),
            charge=mol.charge,
        )

        # Try to build fermionic Hamiltonian
        use_openfermion = False
        try:
            self._fermionic_hamiltonian = qchem.fermionic_hamiltonian(mol)()
            n_qubits = len(self._fermionic_hamiltonian.wires)
        except ValueError:
            use_openfermion = True

        # Select optimal mapping
        if not use_openfermion:
            try:
                self.qubit_hamiltonian, self.mapping = select_optimal_mapping(
                    self._fermionic_hamiltonian
                )
            except Exception:
                use_openfermion = True
                self.mapping = FermionMapping.JORDAN_WIGNER

        # Fall back to OpenFermion if needed
        if use_openfermion:
            self.mapping = FermionMapping.JORDAN_WIGNER

        self.qubit_hamiltonian, n_qubits = qchem.molecular_hamiltonian(
            mol,
            method="openfermion",
            mapping=self.mapping.value
        )

        self.properties = MoleculeProperties(
            n_electrons=mol.n_electrons,
            n_qubits=n_qubits,
            n_orbitals=n_qubits // 2,
            spin=mol.mult - 1,
            charge=mol.charge,
            is_open_shell=(mol.mult != 1)
        )

    def _init_from_pyscf(self) -> None:
        """Initialize from PySCF molecule."""
        mol = self._raw_molecule
        self._pyscf_mol = mol

        self.mapping = FermionMapping.JORDAN_WIGNER

        self.properties = MoleculeProperties(
            n_electrons=mol.nelectron,
            n_qubits=mol.nelectron * 2,
            n_orbitals=mol.nelectron,
            spin=mol.spin,
            charge=mol.charge,
            is_open_shell=(mol.spin != 0)
        )

    @property
    def pyscf_molecule(self) -> pyscf.gto.Mole:
        """Get the PySCF molecule object."""
        return self._pyscf_mol

    @property
    def is_pennylane_source(self) -> bool:
        """Check if molecule was created from PennyLane."""
        return isinstance(self._raw_molecule, qchem.Molecule)

    def get_device(self) -> qml.devices.Device:
        """Create and return the quantum device."""
        return qml.device(self._device_type.value)

    def __repr__(self) -> str:
        name = self.name or "Unnamed"
        return f"MoleculeWrapper(name='{name}', n_electrons={self.properties.n_electrons})"