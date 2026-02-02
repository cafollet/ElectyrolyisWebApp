"""
Molecule-related API endpoints.

Provides molecule validation and preset molecule definitions.
"""

from flask import jsonify, request
from . import api_bp
from ..models.schemas import MoleculeSchema
from ..utils.molecule_builder import MoleculeBuilder

molecule_schema = MoleculeSchema()


@api_bp.route('/molecules/validate', methods=['POST'])
def validate_molecule():
    """
    Validate a molecule definition.

    Checks that the molecule is chemically valid and can be simulated.

    Returns:
        200: Molecule is valid with computed properties
        400: Validation errors
    """
    data = molecule_schema.load(request.get_json())

    builder = MoleculeBuilder()
    validation_result = builder.validate(data)

    return jsonify({
        'valid': validation_result['valid'],
        'molecule_name': data.get('name', ''),
        'num_atoms': len(data['atoms']),
        'num_electrons': validation_result['num_electrons'],
        'num_qubits_required': validation_result['num_qubits'],
        'estimated_vqe_time_seconds': validation_result.get('estimated_vqe_time'),
        'estimated_sqd_time_seconds': validation_result.get('estimated_sqd_time'),
        'warnings': validation_result.get('warnings', []),
        'recommended_method': validation_result.get('recommended_method')
    })


@api_bp.route('/molecules/presets', methods=['GET'])
def get_preset_molecules():
    """
    Get a list of preset molecule definitions.

    Useful for testing and demonstration purposes.

    Returns:
        200: List of preset molecules with their definitions
    """
    presets = {
        'hydrogen': {
            'name': 'Hydrogen (H₂)',
            'description': 'Simplest molecule, good for testing',
            'molecule': {
                'name': 'Hydrogen',
                'atoms': [
                    {'symbol': 'H', 'position': [0.0, 0.0, -0.69434785]},
                    {'symbol': 'H', 'position': [0.0, 0.0, 0.69434785]}
                ],
                'charge': 0,
                'multiplicity': 1,
                'basis_set': 'sto-3g'
            },
            'expected_energy_hartree': -1.137,
            'recommended_method': 'vqe'
        },
        'helium': {
            'name': 'Helium (He)',
            'description': 'Noble gas atom',
            'molecule': {
                'name': 'Helium',
                'atoms': [
                    {'symbol': 'He', 'position': [0.0, 0.0, 0.0]}
                ],
                'charge': 0,
                'multiplicity': 1,
                'basis_set': 'sto-3g'
            },
            'expected_energy_hartree': -2.862,
            'recommended_method': 'vqe'
        },
        'lithium_hydride': {
            'name': 'Lithium Hydride (LiH)',
            'description': 'Simple ionic molecule',
            'molecule': {
                'name': 'Lithium Hydride',
                'atoms': [
                    {'symbol': 'Li', 'position': [0.0, 0.0, 0.0]},
                    {'symbol': 'H', 'position': [0.0, 0.0, 1.5949]}
                ],
                'charge': 0,
                'multiplicity': 1,
                'basis_set': 'sto-3g'
            },
            'expected_energy_hartree': -7.863,
            'recommended_method': 'vqe'
        },
        'water': {
            'name': 'Water (H₂O)',
            'description': 'Common molecule with bent geometry',
            'molecule': {
                'name': 'Water',
                'atoms': [
                    {'symbol': 'O', 'position': [0.0, 0.0, 0.1173]},
                    {'symbol': 'H', 'position': [0.0, 0.7572, -0.4692]},
                    {'symbol': 'H', 'position': [0.0, -0.7572, -0.4692]}
                ],
                'charge': 0,
                'multiplicity': 1,
                'basis_set': 'sto-3g'
            },
            'expected_energy_hartree': -75.0,
            'recommended_method': 'sqd'
        },
        'beryllium': {
            'name': 'Beryllium (Be)',
            'description': 'Small atom for testing',
            'molecule': {
                'name': 'Beryllium',
                'atoms': [
                    {'symbol': 'Be', 'position': [0.0, 0.0, 0.0]}
                ],
                'charge': 0,
                'multiplicity': 1,
                'basis_set': 'sto-3g'
            },
            'expected_energy_hartree': -14.57,
            'recommended_method': 'vqe'
        },
        'lithium_ion': {
            'name': 'Lithium Ion (Li⁺)',
            'description': 'Simple cation',
            'molecule': {
                'name': 'Lithium Ion',
                'atoms': [
                    {'symbol': 'Li', 'position': [0.0, 0.0, 0.0]}
                ],
                'charge': 1,
                'multiplicity': 1,
                'basis_set': 'sto-3g'
            },
            'expected_energy_hartree': -7.236,
            'recommended_method': 'vqe'
        },
        'aluminum': {
            'name': 'Aluminum (Al)',
            'description': 'Larger atom requiring SQD',
            'molecule': {
                'name': 'Aluminum',
                'atoms': [
                    {'symbol': 'Al', 'position': [0.0, 0.0, 0.0]}
                ],
                'charge': 0,
                'multiplicity': 2,
                'basis_set': 'sto-3g'
            },
            'expected_energy_hartree': -240.0,
            'recommended_method': 'sqd'
        }
    }

    return jsonify({
        'presets': presets,
        'count': len(presets)
    })


@api_bp.route('/molecules/elements', methods=['GET'])
def get_supported_elements():
    """
    Get list of supported chemical elements.

    Optionally filter by basis set via ``?basis_set=<name>``.  When a
    basis set is supplied only elements that have data in that set are
    returned.

    Returns:
        200: List of elements with atomic numbers
    """
    from ..utils.molecule_builder import ATOMIC_NUMBERS, _supported_z_set

    # Full periodic-table data (Z 1–118)
    ALL_ELEMENTS = [
        {'symbol': 'H',  'name': 'Hydrogen',      'atomic_number': 1},
        {'symbol': 'He', 'name': 'Helium',        'atomic_number': 2},
        {'symbol': 'Li', 'name': 'Lithium',       'atomic_number': 3},
        {'symbol': 'Be', 'name': 'Beryllium',     'atomic_number': 4},
        {'symbol': 'B',  'name': 'Boron',         'atomic_number': 5},
        {'symbol': 'C',  'name': 'Carbon',        'atomic_number': 6},
        {'symbol': 'N',  'name': 'Nitrogen',      'atomic_number': 7},
        {'symbol': 'O',  'name': 'Oxygen',        'atomic_number': 8},
        {'symbol': 'F',  'name': 'Fluorine',      'atomic_number': 9},
        {'symbol': 'Ne', 'name': 'Neon',          'atomic_number': 10},
        {'symbol': 'Na', 'name': 'Sodium',        'atomic_number': 11},
        {'symbol': 'Mg', 'name': 'Magnesium',     'atomic_number': 12},
        {'symbol': 'Al', 'name': 'Aluminum',      'atomic_number': 13},
        {'symbol': 'Si', 'name': 'Silicon',       'atomic_number': 14},
        {'symbol': 'P',  'name': 'Phosphorus',    'atomic_number': 15},
        {'symbol': 'S',  'name': 'Sulfur',        'atomic_number': 16},
        {'symbol': 'Cl', 'name': 'Chlorine',      'atomic_number': 17},
        {'symbol': 'Ar', 'name': 'Argon',         'atomic_number': 18},
        {'symbol': 'K',  'name': 'Potassium',     'atomic_number': 19},
        {'symbol': 'Ca', 'name': 'Calcium',       'atomic_number': 20},
        {'symbol': 'Sc', 'name': 'Scandium',      'atomic_number': 21},
        {'symbol': 'Ti', 'name': 'Titanium',      'atomic_number': 22},
        {'symbol': 'V',  'name': 'Vanadium',      'atomic_number': 23},
        {'symbol': 'Cr', 'name': 'Chromium',      'atomic_number': 24},
        {'symbol': 'Mn', 'name': 'Manganese',     'atomic_number': 25},
        {'symbol': 'Fe', 'name': 'Iron',          'atomic_number': 26},
        {'symbol': 'Co', 'name': 'Cobalt',        'atomic_number': 27},
        {'symbol': 'Ni', 'name': 'Nickel',        'atomic_number': 28},
        {'symbol': 'Cu', 'name': 'Copper',        'atomic_number': 29},
        {'symbol': 'Zn', 'name': 'Zinc',          'atomic_number': 30},
        {'symbol': 'Ga', 'name': 'Gallium',       'atomic_number': 31},
        {'symbol': 'Ge', 'name': 'Germanium',     'atomic_number': 32},
        {'symbol': 'As', 'name': 'Arsenic',       'atomic_number': 33},
        {'symbol': 'Se', 'name': 'Selenium',      'atomic_number': 34},
        {'symbol': 'Br', 'name': 'Bromine',       'atomic_number': 35},
        {'symbol': 'Kr', 'name': 'Krypton',       'atomic_number': 36},
        {'symbol': 'Rb', 'name': 'Rubidium',      'atomic_number': 37},
        {'symbol': 'Sr', 'name': 'Strontium',     'atomic_number': 38},
        {'symbol': 'Y',  'name': 'Yttrium',       'atomic_number': 39},
        {'symbol': 'Zr', 'name': 'Zirconium',     'atomic_number': 40},
        {'symbol': 'Nb', 'name': 'Niobium',       'atomic_number': 41},
        {'symbol': 'Mo', 'name': 'Molybdenum',    'atomic_number': 42},
        {'symbol': 'Tc', 'name': 'Technetium',    'atomic_number': 43},
        {'symbol': 'Ru', 'name': 'Ruthenium',     'atomic_number': 44},
        {'symbol': 'Rh', 'name': 'Rhodium',       'atomic_number': 45},
        {'symbol': 'Pd', 'name': 'Palladium',     'atomic_number': 46},
        {'symbol': 'Ag', 'name': 'Silver',        'atomic_number': 47},
        {'symbol': 'Cd', 'name': 'Cadmium',       'atomic_number': 48},
        {'symbol': 'In', 'name': 'Indium',        'atomic_number': 49},
        {'symbol': 'Sn', 'name': 'Tin',           'atomic_number': 50},
        {'symbol': 'Sb', 'name': 'Antimony',      'atomic_number': 51},
        {'symbol': 'Te', 'name': 'Tellurium',     'atomic_number': 52},
        {'symbol': 'I',  'name': 'Iodine',        'atomic_number': 53},
        {'symbol': 'Xe', 'name': 'Xenon',         'atomic_number': 54},
        {'symbol': 'Cs', 'name': 'Cesium',        'atomic_number': 55},
        {'symbol': 'Ba', 'name': 'Barium',        'atomic_number': 56},
        {'symbol': 'La', 'name': 'Lanthanum',     'atomic_number': 57},
        {'symbol': 'Ce', 'name': 'Cerium',        'atomic_number': 58},
        {'symbol': 'Pr', 'name': 'Praseodymium',  'atomic_number': 59},
        {'symbol': 'Nd', 'name': 'Neodymium',     'atomic_number': 60},
        {'symbol': 'Pm', 'name': 'Promethium',    'atomic_number': 61},
        {'symbol': 'Sm', 'name': 'Samarium',      'atomic_number': 62},
        {'symbol': 'Eu', 'name': 'Europium',      'atomic_number': 63},
        {'symbol': 'Gd', 'name': 'Gadolinium',    'atomic_number': 64},
        {'symbol': 'Tb', 'name': 'Terbium',       'atomic_number': 65},
        {'symbol': 'Dy', 'name': 'Dysprosium',    'atomic_number': 66},
        {'symbol': 'Ho', 'name': 'Holmium',       'atomic_number': 67},
        {'symbol': 'Er', 'name': 'Erbium',        'atomic_number': 68},
        {'symbol': 'Tm', 'name': 'Thulium',       'atomic_number': 69},
        {'symbol': 'Yb', 'name': 'Ytterbium',     'atomic_number': 70},
        {'symbol': 'Lu', 'name': 'Lutetium',      'atomic_number': 71},
        {'symbol': 'Hf', 'name': 'Hafnium',       'atomic_number': 72},
        {'symbol': 'Ta', 'name': 'Tantalum',      'atomic_number': 73},
        {'symbol': 'W',  'name': 'Tungsten',      'atomic_number': 74},
        {'symbol': 'Re', 'name': 'Rhenium',       'atomic_number': 75},
        {'symbol': 'Os', 'name': 'Osmium',        'atomic_number': 76},
        {'symbol': 'Ir', 'name': 'Iridium',       'atomic_number': 77},
        {'symbol': 'Pt', 'name': 'Platinum',      'atomic_number': 78},
        {'symbol': 'Au', 'name': 'Gold',          'atomic_number': 79},
        {'symbol': 'Hg', 'name': 'Mercury',       'atomic_number': 80},
        {'symbol': 'Tl', 'name': 'Thallium',      'atomic_number': 81},
        {'symbol': 'Pb', 'name': 'Lead',          'atomic_number': 82},
        {'symbol': 'Bi', 'name': 'Bismuth',       'atomic_number': 83},
        {'symbol': 'Po', 'name': 'Polonium',      'atomic_number': 84},
        {'symbol': 'At', 'name': 'Astatine',      'atomic_number': 85},
        {'symbol': 'Rn', 'name': 'Radon',         'atomic_number': 86},
        {'symbol': 'Fr', 'name': 'Francium',      'atomic_number': 87},
        {'symbol': 'Ra', 'name': 'Radium',        'atomic_number': 88},
        {'symbol': 'Ac', 'name': 'Actinium',      'atomic_number': 89},
        {'symbol': 'Th', 'name': 'Thorium',       'atomic_number': 90},
        {'symbol': 'Pa', 'name': 'Protactinium',  'atomic_number': 91},
        {'symbol': 'U',  'name': 'Uranium',       'atomic_number': 92},
        {'symbol': 'Np', 'name': 'Neptunium',     'atomic_number': 93},
        {'symbol': 'Pu', 'name': 'Plutonium',     'atomic_number': 94},
        {'symbol': 'Am', 'name': 'Americium',     'atomic_number': 95},
        {'symbol': 'Cm', 'name': 'Curium',        'atomic_number': 96},
        {'symbol': 'Bk', 'name': 'Berkelium',     'atomic_number': 97},
        {'symbol': 'Cf', 'name': 'Californium',   'atomic_number': 98},
        {'symbol': 'Es', 'name': 'Einsteinium',   'atomic_number': 99},
        {'symbol': 'Fm', 'name': 'Fermium',       'atomic_number': 100},
        {'symbol': 'Md', 'name': 'Mendelevium',   'atomic_number': 101},
        {'symbol': 'No', 'name': 'Nobelium',      'atomic_number': 102},
        {'symbol': 'Lr', 'name': 'Lawrencium',    'atomic_number': 103},
        {'symbol': 'Rf', 'name': 'Rutherfordium', 'atomic_number': 104},
        {'symbol': 'Db', 'name': 'Dubnium',       'atomic_number': 105},
        {'symbol': 'Sg', 'name': 'Seaborgium',    'atomic_number': 106},
        {'symbol': 'Bh', 'name': 'Bohrium',       'atomic_number': 107},
        {'symbol': 'Hs', 'name': 'Hassium',       'atomic_number': 108},
        {'symbol': 'Mt', 'name': 'Meitnerium',    'atomic_number': 109},
        {'symbol': 'Ds', 'name': 'Darmstadtium',  'atomic_number': 110},
        {'symbol': 'Rg', 'name': 'Roentgenium',   'atomic_number': 111},
        {'symbol': 'Cn', 'name': 'Copernicium',   'atomic_number': 112},
        {'symbol': 'Nh', 'name': 'Nihonium',      'atomic_number': 113},
        {'symbol': 'Fl', 'name': 'Flerovium',     'atomic_number': 114},
        {'symbol': 'Mc', 'name': 'Moscovium',     'atomic_number': 115},
        {'symbol': 'Lv', 'name': 'Livermorium',   'atomic_number': 116},
        {'symbol': 'Ts', 'name': 'Tennessine',    'atomic_number': 117},
        {'symbol': 'Og', 'name': 'Oganesson',     'atomic_number': 118},
    ]

    # Optional basis-set filter
    basis_set = request.args.get('basis_set')
    if basis_set:
        allowed_z = _supported_z_set(basis_set.lower())
        elements = [e for e in ALL_ELEMENTS if e['atomic_number'] in allowed_z]
    else:
        elements = ALL_ELEMENTS

    return jsonify({
        'elements': elements,
        'count': len(elements)
    })