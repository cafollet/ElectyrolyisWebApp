"""
Configuration settings and constants for quantum chemistry calculations.

This module defines all configuration dataclasses, enums, and constants
used throughout the quantum chemistry simulation pipeline.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, List


class SimulationMethod(Enum):
    """Available simulation methods for ground state energy calculation."""
    VQE = "vqe"
    SQD = "sqd"


class QubitDevice(Enum):
    """Supported PennyLane qubit devices."""
    DEFAULT_QUBIT = "default.qubit"
    # Future support planned:
    # DEFAULT_MIXED = "default.mixed"
    # LIGHTNING_QUBIT = "lightning.qubit"
    # LIGHTNING_GPU = "lightning.gpu"


class FermionMapping(Enum):
    """Fermion-to-qubit mapping transformations."""
    JORDAN_WIGNER = "jordan_wigner"
    BRAVYI_KITAEV = "bravyi_kitaev"
    PARITY = "parity"


@dataclass(frozen=True)
class VQEConfig:
    """
    Configuration for Variational Quantum Eigensolver (VQE) optimization.

    Attributes:
        step_size: Learning rate for the Adam optimizer.
        num_steps: Maximum number of optimization iterations.
        convergence_threshold: Energy convergence criterion (optional).
        print_interval_fraction: Fraction of steps between progress updates.
    """
    step_size: float = 0.2
    num_steps: int = 200
    convergence_threshold: Optional[float] = None
    print_interval_fraction: float = 0.2

    def __post_init__(self):
        if self.step_size <= 0:
            raise ValueError("step_size must be positive")
        if self.num_steps <= 0:
            raise ValueError("num_steps must be positive")


@dataclass(frozen=True)
class SQDConfig:
    """
    Configuration for Sample-based Quantum Diagonalization (SQD).

    Attributes:
        samples_per_batch: Number of samples in each batch for subsampling.
        max_iterations: Maximum number of SQD iterations.
        num_batches: Number of parallel batches for eigenstate solving.
        num_shots: Number of quantum circuit shots.
        energy_tolerance: Convergence tolerance for energy.
        occupancies_tolerance: Convergence tolerance for occupancies.
        max_scf_cycles: Maximum SCF cycles in eigensolver.
        symmetrize_spin: Whether to enforce spin symmetry.
        carryover_threshold: Threshold for configuration carryover.
        random_seed: Seed for reproducibility.
    """
    samples_per_batch: int = 500
    max_iterations: int = 100
    num_batches: int = 5
    num_shots: int = 10_000
    energy_tolerance: float = 1e-4
    occupancies_tolerance: float = 1e-4
    max_scf_cycles: int = 300
    symmetrize_spin: bool = False
    carryover_threshold: float = 1e-4
    random_seed: int = 12345

    def __post_init__(self):
        if self.samples_per_batch <= 0:
            raise ValueError("samples_per_batch must be positive")
        if self.num_shots <= 0:
            raise ValueError("num_shots must be positive")


@dataclass
class UCJOperatorConfig:
    """Configuration for Unitary Coupled-Cluster operator construction."""
    n_reps: int = 2
    alpha_alpha_step: int = 1
    alpha_beta_step: int = 4


@dataclass
class SimulationResult:
    """
    Container for simulation results.

    Attributes:
        energy: Final computed ground state energy (Hartree).
        energy_history: List of energies throughout optimization/iterations.
        method: The simulation method used.
        mapping: The fermion-to-qubit mapping used.
        converged: Whether the simulation converged.
        num_iterations: Number of iterations performed.
        final_parameters: Optimized parameters (VQE only).
        metadata: Additional simulation metadata.
    """
    energy: float
    energy_history: List[float] = field(default_factory=list)
    method: SimulationMethod = SimulationMethod.VQE
    mapping: Optional[FermionMapping] = None
    converged: bool = False
    num_iterations: int = 0
    final_parameters: Optional[any] = None
    metadata: dict = field(default_factory=dict)