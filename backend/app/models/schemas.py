"""
Marshmallow schemas for request/response validation and serialization.

Provides data validation for API inputs and consistent output formatting.
"""

from marshmallow import Schema, fields, validate, validates_schema, ValidationError, post_load
from typing import Dict, Any, List


class AtomSchema(Schema):
    """Schema for a single atom definition."""

    symbol = fields.String(
        required=True,
        validate=validate.Length(min=1, max=3),
        metadata={'description': 'Atomic symbol (e.g., H, He, Li)'}
    )
    position = fields.List(
        fields.Float(),
        required=True,
        validate=validate.Length(equal=3),
        metadata={'description': '3D coordinates [x, y, z] in Angstroms'}
    )


class MoleculeSchema(Schema):
    """Schema for molecule definition."""

    name = fields.String(
        load_default="",
        metadata={'description': 'Human-readable molecule name'}
    )
    atoms = fields.List(
        fields.Nested(AtomSchema),
        required=True,
        validate=validate.Length(min=1, max=50),
        metadata={'description': 'List of atoms with symbols and positions'}
    )
    charge = fields.Integer(
        load_default=0,
        validate=validate.Range(min=-10, max=10),
        metadata={'description': 'Total molecular charge'}
    )
    multiplicity = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1, max=10),
        metadata={'description': 'Spin multiplicity (2S+1)'}
    )
    basis_set = fields.String(
        load_default="sto-3g",
        validate=validate.OneOf([
            'sto-3g', 'sto-6g', '3-21g', '6-31g', '6-31g*', '6-31g**',
            'cc-pvdz', 'cc-pvtz', 'def2-svp', 'def2-tzvp', 'dyall-ae4z',
        ]),
        metadata={'description': 'Basis set for quantum chemistry calculation'}
    )

    @validates_schema
    def validate_multiplicity(self, data: Dict[str, Any], **kwargs):
        """Validate that multiplicity is consistent with electron count."""
        atoms = data.get('atoms', [])
        charge = data.get('charge', 0)
        multiplicity = data.get('multiplicity', 1)

        # Count electrons (simplified - just sum atomic numbers)
        electron_count = sum(
            _get_atomic_number(atom['symbol'])
            for atom in atoms
        ) - charge

        # Check multiplicity is valid
        if (electron_count + multiplicity) % 2 != 1:
            raise ValidationError(
                f"Invalid multiplicity {multiplicity} for {electron_count} electrons. "
                "Multiplicity must have opposite parity to electron count."
            )

    @validates_schema
    def validate_basis_set_elements(self, data: Dict[str, Any], **kwargs):
        """Validate that every atom is supported by the chosen basis set."""
        atoms = data.get('atoms', [])
        basis_set = data.get('basis_set', 'sto-3g')

        allowed = _supported_z_for_basis(basis_set)
        unsupported = []
        for atom in atoms:
            z = _get_atomic_number(atom['symbol'])
            if z and z not in allowed:
                unsupported.append(atom['symbol'])

        if unsupported:
            unique = list(dict.fromkeys(unsupported))  # preserve order, dedupe
            raise ValidationError(
                f"Element(s) {', '.join(unique)} are not supported by basis set '{basis_set}'."
            )


class VQEConfigSchema(Schema):
    """Schema for VQE simulation configuration."""

    step_size = fields.Float(
        load_default=0.2,
        validate=validate.Range(min=0.001, max=1.0),
        metadata={'description': 'Optimizer learning rate'}
    )
    num_steps = fields.Integer(
        load_default=200,
        validate=validate.Range(min=10, max=5000),
        metadata={'description': 'Maximum optimization iterations'}
    )
    convergence_threshold = fields.Float(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1e-10, max=1e-2),
        metadata={'description': 'Energy convergence threshold (Hartree)'}
    )


class SQDConfigSchema(Schema):
    """Schema for SQD simulation configuration."""

    samples_per_batch = fields.Integer(
        load_default=500,
        validate=validate.Range(min=50, max=10000),
        metadata={'description': 'Samples per batch for subsampling'}
    )
    max_iterations = fields.Integer(
        load_default=100,
        validate=validate.Range(min=5, max=500),
        metadata={'description': 'Maximum SQD iterations'}
    )
    num_batches = fields.Integer(
        load_default=5,
        validate=validate.Range(min=1, max=20),
        metadata={'description': 'Number of parallel batches'}
    )
    num_shots = fields.Integer(
        load_default=10000,
        validate=validate.Range(min=1000, max=100000),
        metadata={'description': 'Number of quantum circuit shots'}
    )
    use_hardware = fields.Boolean(
        load_default=False,
        metadata={'description': 'Use real IBM quantum hardware'}
    )
    ibm_api_key = fields.String(
        load_default=None,
        allow_none=True,
        metadata={'description': 'IBM Quantum API key (not persisted, used only for this job)'}
    )


class SimulationRequestSchema(Schema):
    """Schema for simulation job request."""

    molecule = fields.Nested(
        MoleculeSchema,
        required=True,
        metadata={'description': 'Molecule definition'}
    )
    method = fields.String(
        required=True,
        validate=validate.OneOf(['vqe', 'sqd']),
        metadata={'description': 'Simulation method'}
    )
    vqe_config = fields.Nested(
        VQEConfigSchema,
        load_default=dict,
        metadata={'description': 'VQE-specific configuration'}
    )
    sqd_config = fields.Nested(
        SQDConfigSchema,
        load_default=dict,
        metadata={'description': 'SQD-specific configuration'}
    )


class JobStatusSchema(Schema):
    """Schema for job status response."""

    id = fields.String(metadata={'description': 'Unique job identifier'})
    status = fields.String(metadata={'description': 'Current job status'})
    method = fields.String(metadata={'description': 'Simulation method'})
    molecule_name = fields.String(metadata={'description': 'Molecule name'})
    created_at = fields.DateTime(metadata={'description': 'Job creation time'})
    started_at = fields.DateTime(metadata={'description': 'Job start time'})
    completed_at = fields.DateTime(metadata={'description': 'Job completion time'})
    progress = fields.Integer(metadata={'description': 'Progress percentage'})
    current_step = fields.String(metadata={'description': 'Current processing step'})
    result_energy = fields.Float(metadata={'description': 'Computed ground state energy'})
    energy_history = fields.List(fields.Float(), metadata={'description': 'Energy values per iteration'})
    error_message = fields.String(metadata={'description': 'Error details if failed'})


class SimulationResultSchema(Schema):
    """Schema for complete simulation result."""

    job_id = fields.String(required=True)
    status = fields.String(required=True)
    molecule_name = fields.String()
    method = fields.String()

    # Results
    energy = fields.Float(metadata={'description': 'Final ground state energy (Hartree)'})
    energy_ev = fields.Float(metadata={'description': 'Final ground state energy (eV)'})
    energy_history = fields.List(fields.Float())

    # Metadata
    num_iterations = fields.Integer()
    mapping_used = fields.String()
    converged = fields.Boolean()
    execution_time_seconds = fields.Float()

    # Additional data
    metadata = fields.Dict()


# Helpers

# Basis-set → supported Z ranges (verified against basissetexchange.org)
_BASIS_Z_RANGES: Dict[str, List[tuple]] = {
    'sto-3g':     [(1, 54)],
    'sto-6g':     [(1, 54)],
    '3-21g':      [(1, 55)],
    '6-31g':      [(1, 36)],
    '6-31g*':     [(1, 36)],
    '6-31g**':    [(1, 36)],
    'cc-pvdz':    [(1, 18), (20, 36)],   # K (19) missing
    'cc-pvtz':    [(1, 18), (20, 36)],   # K (19) missing
    'def2-svp':   [(1, 86)],
    'def2-tzvp':  [(1, 86)],
    'dyall-ae4z': [(1, 118)],
}


def _supported_z_for_basis(basis_set: str) -> set:
    """Return the set of atomic numbers supported by *basis_set*."""
    ranges = _BASIS_Z_RANGES.get(basis_set.lower())
    if ranges is None:
        return set(range(1, 119))  # unknown basis → allow all
    s: set = set()
    for lo, hi in ranges:
        s.update(range(lo, hi + 1))
    return s


def _get_atomic_number(symbol: str) -> int:
    """Get atomic number from element symbol (Z 1–118)."""
    periodic_table = {
        'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8,
        'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15,
        'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22,
        'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29,
        'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36,
        'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42, 'Tc': 43,
        'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50,
        'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57,
        'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64,
        'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71,
        'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78,
        'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85,
        'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90, 'Pa': 91, 'U': 92,
        'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99,
        'Fm': 100, 'Md': 101, 'No': 102, 'Lr': 103, 'Rf': 104, 'Db': 105,
        'Sg': 106, 'Bh': 107, 'Hs': 108, 'Mt': 109, 'Ds': 110, 'Rg': 111,
        'Cn': 112, 'Nh': 113, 'Fl': 114, 'Mc': 115, 'Lv': 116, 'Ts': 117,
        'Og': 118,
    }
    return periodic_table.get(symbol, 0)