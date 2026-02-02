"""
Sample-based Quantum Diagonalization (SQD) implementation.

This module implements the SQD algorithm for finding molecular
ground state energies using quantum sampling and classical diagonalization.
"""

from functools import partial
from typing import Optional, List, Tuple
import numpy as np

import pyscf
from pyscf import ao2mo
import ffsim
from qiskit import QuantumCircuit, QuantumRegister
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
import qiskit.transpiler.preset_passmanagers

from qiskit_addon_sqd.fermion import (
    SCIResult,
    diagonalize_fermionic_hamiltonian,
    solve_sci_batch,
)

from .base import BaseSolver
from ..config import SQDConfig, SimulationResult, SimulationMethod, UCJOperatorConfig
from ..molecule import MoleculeWrapper
from ..exceptions import SimulationError, BackendConnectionError


class SQDSolver(BaseSolver):
    """
    Sample-based Quantum Diagonalization solver.

    Implements SQD using Unitary Coupled-Cluster operators
    for initial state preparation and iterative diagonalization.

    Attributes:
        config: SQD configuration parameters.
        ibm_api_key: Optional IBM Quantum API key for real hardware.
    """

    def __init__(
            self,
            molecule: MoleculeWrapper,
            config: SQDConfig,
            ibm_api_key: Optional[str] = None
    ):
        """
        Initialize SQD solver.

        Args:
            molecule: Molecular system to solve.
            config: SQD parameters.
            ibm_api_key: Optional API key for IBM Quantum hardware.
        """
        super().__init__(molecule)
        self.config = config
        self.ibm_api_key = ibm_api_key

        self._active_space_info: dict = {}
        self._nuclear_repulsion: float = 0.0

    def _setup_active_space(self) -> Tuple[np.ndarray, np.ndarray, int, Tuple[int, int]]:
        """
        Configure active space and compute molecular integrals.

        Returns:
            Tuple of (hcore, eri, num_orbitals, nelec).
        """
        mol = self.molecule.pyscf_molecule
        props = self.molecule.properties

        # Run SCF calculation
        if props.is_open_shell:
            scf_result = pyscf.scf.UHF(mol).run()
        else:
            scf_result = pyscf.scf.RHF(mol).run()

        # Run CCSD for amplitudes
        ccsd = pyscf.cc.CCSD(scf_result)
        ccsd.set_frozen()

        n_frozen = ccsd.frozen if ccsd.frozen else 0
        active_space = range(n_frozen, mol.nao_nr())
        num_orbitals = len(active_space)

        # Calculate electron counts in active space
        if len(scf_result.mo_occ.shape) > 1:
            n_electrons = int(sum(
                sum(occ[active_space]) for occ in scf_result.mo_occ
            ))
        else:
            n_electrons = int(sum(scf_result.mo_occ[active_space]))

        num_elec_a = (n_electrons + mol.spin) // 2
        num_elec_b = (n_electrons - mol.spin) // 2
        nelec = (num_elec_a, num_elec_b)

        # Compute integrals
        cas = pyscf.mcscf.CASCI(scf_result, num_orbitals, nelec)
        mo = cas.sort_mo(active_space, base=0)
        hcore, self._nuclear_repulsion = cas.get_h1cas(mo)
        eri = pyscf.ao2mo.restore(1, cas.get_h2cas(mo), num_orbitals)

        # Get CCSD amplitudes
        ccsd.run()

        self._active_space_info = {
            "scf_result": scf_result,
            "ccsd": ccsd,
            "num_orbitals": num_orbitals,
            "nelec": nelec,
            "t1": ccsd.t1,
            "t2": ccsd.t2,
        }

        return hcore, eri, num_orbitals, nelec

    def _build_ucj_operator(self):
        """Build Unitary Coupled-Cluster operator from CCSD amplitudes."""
        info = self._active_space_info
        props = self.molecule.properties

        ucj_config = UCJOperatorConfig()
        num_orbitals = info["num_orbitals"]

        # Define interaction pairs
        alpha_alpha_indices = [
            (p, p + ucj_config.alpha_alpha_step)
            for p in range(num_orbitals - 1)
        ]
        alpha_beta_indices = [
            (p, p)
            for p in range(0, num_orbitals, ucj_config.alpha_beta_step)
        ]

        if props.is_open_shell:
            return ffsim.UCJOpSpinUnbalanced.from_t_amplitudes(
                t2=info["t2"],
                t1=info["t1"],
                n_reps=ucj_config.n_reps,
            )
        else:
            return ffsim.UCJOpSpinBalanced.from_t_amplitudes(
                t2=info["t2"],
                t1=info["t1"],
                n_reps=ucj_config.n_reps,
                interaction_pairs=(alpha_alpha_indices, alpha_beta_indices),
            )

    def _build_circuit(self) -> QuantumCircuit:
        """Construct the quantum circuit for sampling."""
        info = self._active_space_info
        props = self.molecule.properties

        num_orbitals = info["num_orbitals"]
        nelec = info["nelec"]

        qubits = QuantumRegister(2 * num_orbitals, name="q")
        circuit = QuantumCircuit(qubits)

        # Initialize Hartree-Fock state
        circuit.append(
            ffsim.qiskit.PrepareHartreeFockJW(num_orbitals, nelec),
            qubits
        )

        # Apply UCJ operator
        ucj_op = self._build_ucj_operator()

        if props.is_open_shell:
            circuit.append(ffsim.qiskit.UCJOpSpinUnbalancedJW(ucj_op), qubits)
        else:
            circuit.append(ffsim.qiskit.UCJOpSpinBalancedJW(ucj_op), qubits)

        circuit.measure_all()
        return circuit

    def _get_backend(self):
        """Get quantum backend_b (simulator or real hardware)."""
        if self.ibm_api_key:
            try:
                service = QiskitRuntimeService(token=self.ibm_api_key)
                return service.least_busy(operational=True, simulator=False)
            except Exception as e:
                raise BackendConnectionError(
                    f"Failed to connect to IBM Quantum: {e}"
                ) from e
        else:
            return AerSimulator(method='automatic')

    def _run_quantum_circuit(self, circuit: QuantumCircuit):
        """Execute quantum circuit and return measurement results."""
        backend = self._get_backend()

        # Transpile circuit
        pass_manager = qiskit.transpiler.preset_passmanagers.generate_preset_pass_manager(
            optimization_level=3,
            backend=backend,
        )
        pass_manager.pre_init = ffsim.qiskit.PRE_INIT
        isa_circuit = pass_manager.run(circuit)

        # Run sampling
        sampler = Sampler(mode=backend)
        sampler.options.dynamical_decoupling.enable = True

        job = sampler.run([isa_circuit], shots=self.config.num_shots)
        result = job.result()

        return result[0]

    def _create_callback(self, result_history: List) -> callable:
        """Create callback for iteration progress tracking."""

        def callback(results: List[SCIResult]):
            result_history.append(results)
            iteration = len(result_history)

            self._log_progress(f"Iteration {iteration}")

            for i, result in enumerate(results):
                energy = result.energy + self._nuclear_repulsion
                subspace_dim = np.prod(result.sci_state.amplitudes.shape)

                self._log_progress(
                    f"  Subsample {i}: Energy = {energy:.8f} Ha, "
                    f"Subspace dim = {subspace_dim}"
                )

        return callback

    def solve(self) -> SimulationResult:
        """
        Execute SQD algorithm to find ground state energy.

        Returns:
            SimulationResult with computed energies from all iterations.
        """
        # Setup active space and compute integrals
        hcore, eri, num_orbitals, nelec = self._setup_active_space()

        self._log_progress(f"Running SQD for {self.molecule.name or 'molecule'}")
        self._log_progress(f"Active space: {num_orbitals} orbitals, {sum(nelec)} electrons")

        # Build and run quantum circuit
        circuit = self._build_circuit()
        self._log_progress("Executing quantum circuit...")
        pub_result = self._run_quantum_circuit(circuit)
        self._log_progress("Quantum sampling complete")

        # SQD post-processing
        self._log_progress("Starting SQD post-processing...")

        result_history: List = []
        callback = self._create_callback(result_history)

        sci_solver = partial(
            solve_sci_batch,
            max_cycle=self.config.max_scf_cycles
        )

        diagonalize_fermionic_hamiltonian(
            hcore,
            eri,
            pub_result.data.meas,
            samples_per_batch=self.config.samples_per_batch,
            norb=num_orbitals,
            nelec=nelec,
            num_batches=self.config.num_batches,
            energy_tol=self.config.energy_tolerance,
            occupancies_tol=self.config.occupancies_tolerance,
            max_iterations=self.config.max_iterations,
            sci_solver=sci_solver,
            symmetrize_spin=self.config.symmetrize_spin,
            carryover_threshold=self.config.carryover_threshold,
            callback=callback,
            seed=self.config.random_seed,
        )

        # Extract energy history
        energy_history = [
            min(batch, key=lambda r: r.energy).energy + self._nuclear_repulsion
            for batch in result_history
        ]

        final_energy = min(energy_history) if energy_history else float('inf')

        self._log_progress(f"Final ground state energy (SQD): {final_energy:.8f} Ha")

        return SimulationResult(
            energy=final_energy,
            energy_history=energy_history,
            method=SimulationMethod.SQD,
            mapping=self.molecule.mapping,
            converged=len(energy_history) > 0,
            num_iterations=len(result_history),
            metadata={
                "num_orbitals": num_orbitals,
                "nelec": nelec,
                "nuclear_repulsion": self._nuclear_repulsion,
            }
        )