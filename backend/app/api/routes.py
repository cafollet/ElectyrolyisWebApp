"""
General API routes.

Provides utility endpoints and API information.
"""

from flask import jsonify, current_app
from . import api_bp
from ..logging_config import get_logger
from ..services.job_manager import JobManager

logger = get_logger('app.api.routes')


@api_bp.route('/')
def api_info():
    """
    Get API information and available endpoints.
    """
    logger.debug("API info requested")

    return jsonify({
        'name': 'Quantum Chemistry API',
        'version': '1.0.0',
        'description': 'API for computing molecular ground state energies using quantum algorithms',
        'endpoints': {
            'POST /api/v1/simulations': 'Submit a new simulation job',
            'GET /api/v1/simulations/<job_id>': 'Get job status and results',
            'GET /api/v1/simulations': 'List all jobs',
            'DELETE /api/v1/simulations/<job_id>': 'Cancel a job',
            'GET /api/v1/molecules/presets': 'Get preset molecule definitions',
            'POST /api/v1/molecules/validate': 'Validate a molecule definition',
        },
        'supported_methods': ['vqe', 'sqd'],
        'debug_endpoints': {
            'GET /debug/status': 'System status',
            'GET /api/v1/simulations/debug/active': 'Active job threads',
        }
    })


@api_bp.route('/config')
def get_config():
    """
    Get current API configuration limits.
    """
    logger.debug("Config requested")

    return jsonify({
        'max_atoms': 50,
        'supported_basis_sets': [
            'sto-3g', 'sto-6g', '3-21g', '6-31g', '6-31g*', '6-31g**',
            'cc-pvdz', 'cc-pvtz', 'def2-svp', 'def2-tzvp', 'dyall-ae4z',
        ],
        'vqe_limits': {
            'max_steps': 5000,
            'min_step_size': 0.001,
            'max_step_size': 1.0
        },
        'sqd_limits': {
            'max_iterations': 500,
            'max_shots': 100000,
            'max_samples_per_batch': 10000
        },
        'rate_limit_per_minute': current_app.config['RATE_LIMIT_PER_MINUTE']
    })


@api_bp.route('/debug/threads')
def debug_threads():
    """Debug endpoint to check thread status."""
    import threading

    threads = []
    for thread in threading.enumerate():
        threads.append({
            'name': thread.name,
            'daemon': thread.daemon,
            'alive': thread.is_alive()
        })

    job_manager = JobManager()
    active_jobs = job_manager.get_active_jobs()

    return jsonify({
        'thread_count': threading.active_count(),
        'threads': threads,
        'active_simulation_jobs': active_jobs
    })