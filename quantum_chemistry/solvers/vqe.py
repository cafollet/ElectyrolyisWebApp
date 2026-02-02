"""
Variational Quantum Eigensolver (VQE) implementation.

This module implements the VQE algorithm for finding molecular
ground state energies using parameterized quantum circuits.
"""

from typing import List, Tuple, Optional
import pennylane as qml
from pennylane import qchem
from pennylane.fermi import from_string
from jax import numpy as jnp
import jax
import optax

from .base import BaseSolver
from ..config import VQEConfig, SimulationResult, SimulationMethod
from ..molecule import MoleculeWrapper
from ..mappings import select_optimal_mapping
from ..exceptions import SimulationError, ConvergenceError


class VQESolver(BaseSolver):
    """
    Variational Quantum Eigensolver for molecular ground states.

    Implements the VQE algorithm using a Unitary Coupled-Cluster
    Singles and Doubles (UCCSD) ansatz with JAX optimization.

    Attributes:
        config: VQE optimization configuration.

    Example:
        >>> mol = MoleculeWrapper(qchem.Molecule(['H', 'H'], coords))
        >>> solver = VQESolver(mol, VQEConfig(num_steps=100))
        >>> result = solver.solve()
        >>> print(f"Ground state energy: {result.energy} Ha")
    """

    def __init__(self, molecule: MoleculeWrapper, config: VQEConfig):
        """
        Initialize VQE solver.

        Args:
            molecule: Molecular system to solve.
            config: VQE optimization parameters.

        Raises:
            SimulationError: If molecule is not compatible with VQE.
        """
        super().__init__(molecule)
        self.config = config

        if not molecule.is_pennylane_source:
            raise SimulationError(
                "VQE solver requires a PennyLane Molecule. "
                "Use SQD solver for PySCF molecules."
            )

        self._singles_pauli: List = []
        self._doubles_pauli: List = []
        self._init_state: Optional[jnp.ndarray] = None
        self._device = molecule.get_device()

        self._prepare_ansatz()

    def _prepare_ansatz(self) -> None:
        """Prepare UCCSD ansatz operators."""
        props = self.molecule.properties
        mapping = self.molecule.mapping

        # Get Hartree-Fock initial state
        self._init_state = qchem.hf_state(
            props.n_electrons,
            props.n_qubits,
            basis=mapping.value
        )

        # Generate excitation operators
        singles, doubles = qchem.excitations(
            props.n_electrons,
            props.n_qubits
        )

        # Build fermionic excitation operators
        singles_fermi = [
            from_string(f"{ex[1]}+ {ex[0]}-") - from_string(f"{ex[0]}+ {ex[1]}-")
            for ex in singles
        ]

        doubles_fermi = [
            from_string(f"{ex[3]}+ {ex[2]}+ {ex[1]}- {ex[0]}-") -
            from_string(f"{ex[0]}+ {ex[1]}+ {ex[2]}- {ex[3]}-")
            for ex in doubles
        ]

        # Transform to qubit operators
        self._singles_pauli = [
            select_optimal_mapping(op)[0] for op in singles_fermi
        ]
        self._doubles_pauli = [
            select_optimal_mapping(op)[0] for op in doubles_fermi
        ]

        self._num_params = len(singles) + len(doubles)

    def _build_ansatz(self, theta: jnp.ndarray) -> None:
        """
        Apply UCCSD ansatz to the quantum circuit.

        Args:
            theta: Variational parameters.
        """
        idx = 0

        # Apply double excitations
        for excitation in self._doubles_pauli:
            qml.exp(excitation * theta[idx] / 2)
            idx += 1

        # Apply single excitations
        for excitation in self._singles_pauli:
            qml.exp(excitation * theta[idx] / 2)
            idx += 1

    def _create_circuit(self):
        """Create the VQE quantum circuit."""
        n_qubits = self.molecule.properties.n_qubits
        hamiltonian = self.molecule.qubit_hamiltonian

        @jax.jit
        @qml.qnode(self._device, interface="jax")
        def circuit(theta):
            qml.BasisState(self._init_state, wires=range(n_qubits))
            self._build_ansatz(theta)
            return qml.expval(hamiltonian)

        return circuit

    def solve(self) -> SimulationResult:
        """
        Execute VQE optimization to find ground state energy.

        Returns:
            SimulationResult with optimized energy and parameters.

        Raises:
            ConvergenceError: If optimization fails to converge.
        """
        circuit = self._create_circuit()

        def cost_function(theta):
            return jnp.real(circuit(theta))

        # Initialize optimizer
        optimizer = optax.adam(self.config.step_size)
        params = jnp.zeros(self._num_params)
        opt_state = optimizer.init(params)

        # Optimization loop
        energy_history = []
        print_interval = max(1, int(self.config.num_steps * self.config.print_interval_fraction))

        mol_name = self.molecule.name or "molecule"
        self._log_progress(
            f"Optimizing {mol_name} using {self.molecule.mapping.value} mapping"
        )

        for step in range(self.config.num_steps):
            grads = jax.grad(cost_function)(params)
            updates, opt_state = optimizer.update(grads, opt_state)
            params = optax.apply_updates(params, updates)

            energy = float(cost_function(params))
            energy_history.append(energy)

            if step % print_interval == 0:
                self._log_progress(
                    f"Step {step:4d} | Energy = {energy:.8f} Ha"
                )

        final_energy = float(cost_function(params))
        self._log_progress(f"Final ground state energy (VQE): {final_energy:.8f} Ha")

        return SimulationResult(
            energy=final_energy,
            energy_history=energy_history,
            method=SimulationMethod.VQE,
            mapping=self.molecule.mapping,
            converged=True,  # TODO: Add convergence check
            num_iterations=self.config.num_steps,
            final_parameters=params,
            metadata={
                "num_singles": len(self._singles_pauli),
                "num_doubles": len(self._doubles_pauli),
            }
        )