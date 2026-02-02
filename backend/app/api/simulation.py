"""
Simulation API endpoints.

Handles job submission, status tracking, and result retrieval.
"""

from flask import jsonify, request
from datetime import datetime
import uuid

from . import api_bp
from .errors import JobNotFoundError, APIError
from ..extensions import db, socketio
from ..models.job import SimulationJob, JobStatus
from ..models.schemas import SimulationRequestSchema
from ..services.job_manager import JobManager
from ..logging_config import get_logger

logger = get_logger('app.api.simulation')

# Schema instances
simulation_request_schema = SimulationRequestSchema()


@api_bp.route('/simulations', methods=['POST'])
def create_simulation():
    """
    Submit a new simulation job.
    """
    logger.info("Received simulation creation request")

    try:
        # Validate request data
        raw_data = request.get_json()
        logger.debug(f"Raw request data: {raw_data}")

        data = simulation_request_schema.load(raw_data)
        logger.debug(f"Validated data: {data}")

    except Exception as e:
        logger.error(f"Request validation failed: {e}")
        raise

    # Create job record
    job_id = str(uuid.uuid4())
    logger.info(f"Creating job with ID: {job_id}")

    job = SimulationJob(
        id=job_id,
        status=JobStatus.PENDING.value,
        method=data['method'],
        molecule_name=data['molecule'].get('name', ''),
        molecule_data=data['molecule'],
        config_data={
            'vqe_config': data.get('vqe_config', {}),
            'sqd_config': data.get('sqd_config', {})
        }
    )

    try:
        db.session.add(job)
        db.session.commit()
        logger.info(f"Job {job_id} saved to database")
    except Exception as e:
        logger.error(f"Failed to save job to database: {e}")
        db.session.rollback()
        raise

    # Submit job for processing
    try:
        logger.debug(f"Submitting job {job_id} to JobManager...")
        job_manager = JobManager()
        job_manager.submit_job(job_id)
        logger.info(f"Job {job_id} submitted successfully")
    except Exception as e:
        logger.error(f"Failed to submit job {job_id}: {e}")
        # Update job status to failed
        job.status = JobStatus.FAILED.value
        job.error_message = f"Failed to start: {str(e)}"
        db.session.commit()
        raise

    return jsonify({
        'message': 'Simulation job created',
        'job_id': job_id,
        'status': JobStatus.PENDING.value,
        'status_url': f'/api/v1/simulations/{job_id}'
    }), 201


@api_bp.route('/simulations/<job_id>', methods=['GET'])
def get_simulation_status(job_id: str):
    """
    Get the status and results of a simulation job.
    """
    logger.debug(f"Getting status for job {job_id}")

    job = SimulationJob.query.get(job_id)

    if not job:
        logger.warning(f"Job {job_id} not found")
        raise JobNotFoundError(job_id)

    response_data = job.to_dict()

    # Add additional result data if completed
    if job.status == JobStatus.COMPLETED.value and job.result_data:
        response_data['result'] = job.result_data

        # Add energy in eV
        if job.result_energy:
            response_data['energy_ev'] = job.result_energy * 27.2114

    logger.debug(f"Job {job_id} status: {job.status}")
    return jsonify(response_data)


@api_bp.route('/simulations', methods=['GET'])
def list_simulations():
    """
    List all simulation jobs.
    """
    logger.debug("Listing simulations")

    status_filter = request.args.get('status')
    limit = min(int(request.args.get('limit', 20)), 100)
    offset = int(request.args.get('offset', 0))

    query = SimulationJob.query

    if status_filter:
        query = query.filter_by(status=status_filter)
        logger.debug(f"Filtering by status: {status_filter}")

    total = query.count()
    jobs = query.order_by(SimulationJob.created_at.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()

    logger.debug(f"Found {len(jobs)} jobs (total: {total})")

    return jsonify({
        'jobs': [job.to_dict() for job in jobs],
        'total': total,
        'limit': limit,
        'offset': offset,
        'has_more': offset + limit < total
    })


@api_bp.route('/simulations/<job_id>', methods=['DELETE'])
def cancel_simulation(job_id: str):
    """
    Cancel a pending or running simulation job.
    """
    logger.info(f"Cancel request for job {job_id}")

    job = SimulationJob.query.get(job_id)

    if not job:
        logger.warning(f"Job {job_id} not found for cancellation")
        raise JobNotFoundError(job_id)

    if job.status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
        logger.warning(f"Cannot cancel job {job_id} with status {job.status}")
        raise APIError(
            message=f"Cannot cancel job with status: {job.status}",
            status_code=400
        )

    # Cancel the job
    job_manager = JobManager()
    job_manager.cancel_job(job_id)

    job.status = JobStatus.CANCELLED.value
    job.completed_at = datetime.utcnow()
    db.session.commit()

    logger.info(f"Job {job_id} cancelled")

    return jsonify({
        'message': 'Job cancelled',
        'job_id': job_id,
        'status': JobStatus.CANCELLED.value
    })


@api_bp.route('/simulations/<job_id>/energy-history', methods=['GET'])
def get_energy_history(job_id: str):
    """
    Get the energy convergence history for a job.
    """
    logger.debug(f"Getting energy history for job {job_id}")

    job = SimulationJob.query.get(job_id)

    if not job:
        raise JobNotFoundError(job_id)

    return jsonify({
        'job_id': job_id,
        'method': job.method,
        'energy_history': job.energy_history or [],
        'final_energy': job.result_energy,
        'unit': 'Hartree'
    })


@api_bp.route('/simulations/debug/active', methods=['GET'])
def get_active_jobs():
    """Debug endpoint to get active jobs."""
    logger.debug("Getting active jobs")

    job_manager = JobManager()
    active = job_manager.get_active_jobs()

    return jsonify({
        'active_jobs': active,
        'count': len(active)
    })