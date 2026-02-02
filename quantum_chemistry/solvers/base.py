"""Base class for quantum chemistry solvers."""

from abc import ABC, abstractmethod
from typing import Optional, Callable

from ..config import SimulationResult
from ..molecule import MoleculeWrapper


class BaseSolver(ABC):
    """
    Abstract base class for ground state energy solvers.

    All solver implementations should inherit from this class
    and implement the `solve` method.
    """

    def __init__(self, molecule: MoleculeWrapper):
        """
        Initialize solver with a molecule.

        Args:
            molecule: The molecular system to solve.
        """
        self.molecule = molecule
        self._callback: Optional[Callable] = None

    def set_callback(self, callback: Callable) -> None:
        """
        Set a callback function for progress updates.

        Args:
            callback: Function called with progress updates.
        """
        self._callback = callback

    @abstractmethod
    def solve(self) -> SimulationResult:
        """
        Compute the ground state energy.

        Returns:
            SimulationResult containing the computed energy and metadata.
        """
        pass

    def _log_progress(self, message: str) -> None:
        """Log progress message, using callback if available."""
        if self._callback:
            self._callback(message)
        else:
            print(message)