"""
Fermion-to-qubit mapping utilities.

This module provides functions for transforming fermionic Hamiltonians
to qubit Hamiltonians using various mapping schemes.
"""

from typing import Tuple, Dict, Any
import pennylane as qml
from pennylane import jordan_wigner, bravyi_kitaev
from pennylane.fermi import parity_transform, FermiSentence

from .config import FermionMapping
from .exceptions import MappingError


def apply_mapping(
        fermion_op: FermiSentence,
        mapping: FermionMapping,
        n_qubits: int
) -> qml.Hamiltonian:
    """
    Apply a specific fermion-to-qubit mapping.

    Args:
        fermion_op: The fermionic operator to transform.
        mapping: The mapping scheme to use.
        n_qubits: Number of qubits (required for some mappings).

    Returns:
        The transformed qubit Hamiltonian.

    Raises:
        MappingError: If the mapping fails.
    """
    try:
        if mapping == FermionMapping.JORDAN_WIGNER:
            return jordan_wigner(fermion_op)
        elif mapping == FermionMapping.BRAVYI_KITAEV:
            return bravyi_kitaev(fermion_op, n_qubits)
        elif mapping == FermionMapping.PARITY:
            return parity_transform(fermion_op, n=n_qubits)
        else:
            raise MappingError(f"Unknown mapping: {mapping}")
    except Exception as e:
        raise MappingError(f"Mapping failed: {e}") from e


def select_optimal_mapping(
        fermion_hamiltonian: FermiSentence
) -> Tuple[qml.Hamiltonian, FermionMapping]:
    """
    Select the optimal fermion-to-qubit mapping based on arithmetic depth.

    Evaluates Jordan-Wigner, Bravyi-Kitaev, and Parity transformations,
    returning the one with minimal arithmetic depth for efficient simulation.

    Args:
        fermion_hamiltonian: The fermionic Hamiltonian to map.

    Returns:
        Tuple containing:
            - best_hamiltonian: Qubit Hamiltonian with minimal depth.
            - best_mapping: The mapping that produced the optimal result.

    Raises:
        MappingError: If all mappings fail.
    """
    if not fermion_hamiltonian.wires:
        raise MappingError("Fermionic Hamiltonian has no wires defined")

    n_qubits = max(fermion_hamiltonian.wires) + 1

    mapping_functions = {
        FermionMapping.JORDAN_WIGNER: lambda h: jordan_wigner(h),
        FermionMapping.BRAVYI_KITAEV: lambda h: bravyi_kitaev(h, n_qubits),
        FermionMapping.PARITY: lambda h: parity_transform(h, n=n_qubits),
    }

    results: Dict[FermionMapping, Dict[str, Any]] = {}

    for mapping, transform in mapping_functions.items():
        try:
            qubit_hamiltonian = transform(fermion_hamiltonian)
            depth = qubit_hamiltonian.arithmetic_depth
            results[mapping] = {
                "hamiltonian": qubit_hamiltonian,
                "depth": depth,
            }
        except Exception as e:
            # Log warning but continue trying other mappings
            continue

    if not results:
        raise MappingError("All mapping transformations failed")

    # Select mapping with minimum arithmetic depth
    best_mapping = min(results, key=lambda k: results[k]["depth"])
    best_hamiltonian = results[best_mapping]["hamiltonian"]

    return best_hamiltonian, best_mapping