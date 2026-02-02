"""
Main simulator interface for quantum chemistry calculations.

This module provides the high-level API for running ground state
energy calculations using various quantum methods.
"""

from typing import Union, Optional

import jax

from .config import (
    SimulationMethod,
    VQEConfig,
    SQDConfig,
    SimulationResult,
)
from .molecule import MoleculeWrapper, MoleculeInput
from .solvers.vqe import VQESolver
from .solvers.sqd import SQDSolver
from .exceptions import SimulationError

# Enable 64-bit precision for JAX
jax.config.update("jax_enable_x64", True)


class GroundStateSimulator:
    """
    High-level interface for ground state energy calculations.

    Provides a unified API for running VQE or SQD simulations
    on molecular systems.

    Example:
        >>> from quantum_chemistry import GroundStateSimulator
        >>> from pennylane import qchem
        >>>
        >>> mol = qchem.Molecule(['H', 'H'], [[0,0,-0.7], [0,0,0.7]])
        >>> sim = GroundStateSimulator()
        >>> result = sim.run(mol, method='vqe')
        >>> print(f"Energy: {result.energy} Ha")
    """

    def __init__(self, ibm_api_key: Optional[str] = None):
        """
        Initialize simulator.

        Args:
            ibm_api_key: Optional IBM Quantum API key for hardware access.
        """
        self.ibm_api_key = ibm_api_key

    def run(
            self,
            molecule: MoleculeInput,
            method: Union[SimulationMethod, str] = SimulationMethod.VQE,
            name: str = "",
            vqe_config: Optional[VQEConfig] = None,
            sqd_config: Optional[SQDConfig] = None,
    ) -> SimulationResult:
        """
        Run ground state energy calculation.

        Args:
            molecule: Molecular system (PennyLane or PySCF format).
            method: Simulation method ('vqe' or 'sqd').
            name: Optional name for the molecule.
            vqe_config: VQE-specific configuration.
            sqd_config: SQD-specific configuration.

        Returns:
            SimulationResult containing computed energy and metadata.

        Raises:
            SimulationError: If simulation fails or method is invalid.
        """
        # Convert string method to enum
        if isinstance(method, str):
            try:
                method = SimulationMethod(method.lower())
            except ValueError:
                raise SimulationError(
                    f"Unknown method: {method}. Use 'vqe' or 'sqd'."
                )

        # Wrap molecule
        mol_wrapper = MoleculeWrapper(molecule, name=name)

        # Select and run solver
        if method == SimulationMethod.VQE:
            config = vqe_config or VQEConfig()
            solver = VQESolver(mol_wrapper, config)
        elif method == SimulationMethod.SQD:
            config = sqd_config or SQDConfig()
            solver = SQDSolver(mol_wrapper, config, self.ibm_api_key)
        else:
            raise SimulationError(f"Unsupported method: {method}")

        return solver.solve()

    def compute_adsorption_energy(
            self,
            adsorbate: MoleculeInput,
            surface: MoleculeInput,
            combined: MoleculeInput,
            method: Union[SimulationMethod, str] = SimulationMethod.SQD,
            **kwargs
    ) -> float:
        """
        Compute adsorption energy: E_ads = E_combined - E_surface - E_adsorbate.

        Args:
            adsorbate: The adsorbate molecule.
            surface: The surface/substrate.
            combined: The combined adsorbate-surface system.
            method: Simulation method to use.
            **kwargs: Additional arguments passed to run().

        Returns:
            Adsorption energy in Hartree.
        """
        ads_result = self.run(adsorbate, method=method, name="adsorbate", **kwargs)
        surf_result = self.run(surface, method=method, name="surface", **kwargs)
        combo_result = self.run(combined, method=method, name="combined", **kwargs)

        return combo_result.energy - surf_result.energy - ads_result.energy