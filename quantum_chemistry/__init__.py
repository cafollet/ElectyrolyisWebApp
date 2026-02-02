"""
Quantum Chemistry Ground State Energy Calculator

A package for computing molecular ground state energies using
quantum computing methods (VQE, SQD).
"""

from .config import (
    SimulationMethod,
    VQEConfig,
    SQDConfig,
    SimulationResult,
    FermionMapping,
)
from .molecule import MoleculeWrapper
from .simulator import GroundStateSimulator
from .exceptions import (
    QuantumChemistryError,
    SimulationError,
    MoleculeConfigurationError,
)

__version__ = "0.1.0"
__all__ = [
    "GroundStateSimulator",
    "MoleculeWrapper",
    "SimulationMethod",
    "VQEConfig",
    "SQDConfig",
    "SimulationResult",
    "FermionMapping",
    "QuantumChemistryError",
    "SimulationError",
    "MoleculeConfigurationError",
]