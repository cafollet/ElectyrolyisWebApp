"""
Test suite for quantum chemistry simulations.

Run with: pytest tests/test_molecules.py -v
"""

import pytest
import numpy as np
from jax import numpy as jnp
import pennylane as qml
from pennylane import qchem
import pyscf

from quantum_chemistry import (
    GroundStateSimulator,
    VQEConfig,
    SQDConfig,
    SimulationMethod,
)


class TestMoleculeDefinitions:
    """Test molecule definitions for various systems."""

    @staticmethod
    def hydrogen_molecule():
        """H2 molecule."""
        symbols = ['H', 'H']
        geometry = jnp.array([
            [0.0, 0.0, -0.69434785],
            [0.0, 0.0, 0.69434785]
        ])
        return qchem.Molecule(symbols, geometry)

    @staticmethod
    def lithium_atom():
        """Li atom (doublet)."""
        return qchem.Molecule(['Li'], jnp.array([[0.0, 0.0, 0.0]]), mult=2)

    @staticmethod
    def beryllium_atom():
        """Be atom."""
        return qchem.Molecule(['Be'], jnp.array([[0.0, 0.0, 0.0]]))

    @staticmethod
    def hydrogen_pyscf():
        """H2 molecule using PySCF."""
        mol = pyscf.gto.Mole()
        mol.build(
            atom=[["H", (0, 0, -0.69434785)], ["H", (0, 0, 0.69434785)]],
            basis="sto-3g",
        )
        return mol

    @staticmethod
    def aluminum_atom():
        """Al atom (doublet)."""
        mol = pyscf.gto.Mole()
        mol.build(
            atom=[["Al", (0, 0, 0)]],
            basis="sto-3g",
            spin=1,
        )
        return mol


class TestVQE:
    """Tests for VQE solver."""

    def test_hydrogen_vqe(self):
        """Test VQE on hydrogen molecule."""
        sim = GroundStateSimulator()
        config = VQEConfig(step_size=0.2, num_steps=50)

        mol = TestMoleculeDefinitions.hydrogen_molecule()
        result = sim.run(mol, method="vqe", name="H2", vqe_config=config)

        # H2 ground state ~-1.137 Ha
        assert result.energy < -1.0
        assert result.method == SimulationMethod.VQE
        assert len(result.energy_history) == config.num_steps

    def test_beryllium_vqe(self):
        """Test VQE on beryllium atom."""
        sim = GroundStateSimulator()
        config = VQEConfig(step_size=0.2, num_steps=50)

        mol = TestMoleculeDefinitions.beryllium_atom()
        result = sim.run(mol, method="vqe", name="Be", vqe_config=config)

        assert result.energy < 0
        assert result.converged


class TestSQD:
    """Tests for SQD solver."""

    def test_hydrogen_sqd(self):
        """Test SQD on hydrogen molecule."""
        sim = GroundStateSimulator()
        config = SQDConfig(
            samples_per_batch=100,
            max_iterations=10,
            num_shots=1000
        )

        mol = TestMoleculeDefinitions.hydrogen_pyscf()
        result = sim.run(mol, method="sqd", name="H2", sqd_config=config)

        # H2 ground state ~-1.137 Ha
        assert result.energy < -1.0
        assert result.method == SimulationMethod.SQD

    def test_aluminum_sqd(self):
        """Test SQD on aluminum atom."""
        sim = GroundStateSimulator()
        config = SQDConfig(
            samples_per_batch=100,
            max_iterations=10,
            num_shots=1000
        )

        mol = TestMoleculeDefinitions.aluminum_atom()
        result = sim.run(mol, method="sqd", name="Al", sqd_config=config)

        assert result.energy < 0


# Convenience functions for quick testing
def run_hydrogen_test():
    """Quick hydrogen molecule test."""
    sim = GroundStateSimulator()
    mol = TestMoleculeDefinitions.hydrogen_pyscf()
    result = sim.run(mol, method="sqd", name="H2")
    print(f"Hydrogen energy: {result.energy:.6f} Ha")
    return result


def run_aluminum_test():
    """Quick aluminum atom test."""
    sim = GroundStateSimulator()
    mol = TestMoleculeDefinitions.aluminum_atom()
    result = sim.run(mol, method="sqd", name="Al")
    print(f"Aluminum energy: {result.energy:.6f} Ha")
    return result


if __name__ == "__main__":
    import jax

    jax.config.update("jax_enable_x64", True)

    print("=" * 50)
    print("Running Quantum Chemistry Tests")
    print("=" * 50)

    h_result = run_hydrogen_test()
    print(f"\nHydrogen: {min(h_result.energy_history):.6f} Ha")

    al_result = run_aluminum_test()
    print(f"Aluminum: {min(al_result.energy_history):.6f} Ha")