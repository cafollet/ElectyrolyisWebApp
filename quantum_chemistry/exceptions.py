"""Custom exceptions for quantum chemistry simulations."""


class QuantumChemistryError(Exception):
    """Base exception for quantum chemistry module."""
    pass


class MoleculeConfigurationError(QuantumChemistryError):
    """Raised when molecule configuration is invalid."""
    pass


class SimulationError(QuantumChemistryError):
    """Raised when simulation fails to complete."""
    pass


class MappingError(QuantumChemistryError):
    """Raised when fermion-to-qubit mapping fails."""
    pass


class BackendConnectionError(QuantumChemistryError):
    """Raised when connection to quantum backend_b fails."""
    pass


class ConvergenceError(QuantumChemistryError):
    """Raised when optimization fails to converge."""
    pass