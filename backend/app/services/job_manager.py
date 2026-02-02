"""
Job management service.

Handles job queuing, execution, and status tracking.
"""

from datetime import datetime
from typing import Optional, Callable
import threading
import traceback

from ..extensions import db, socketio
from ..models.job import SimulationJob, JobStatus
from ..logging_config import get_logger

logger = get_logger('app.job_manager')


class JobManager:
    """
    Manages simulation job lifecycle.

    Supports both synchronous execution (for development) and
    asynchronous execution via Celery (for production).
    """

    _instance = None
    _active_jobs: dict = {}

    def __new__(cls):
        """Singleton pattern for job manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.debug("JobManager singleton created")
        return cls._instance

    def submit_job(self, job_id: str, use_celery: bool = False) -> None:
        """
        Submit a job for processing.

        Args:
            job_id: Unique job identifier.
            use_celery: Whether to use Celery for async processing.
        """
        logger.info(f"Submitting job {job_id} (use_celery={use_celery})")

        if use_celery:
            self._submit_celery(job_id)
        else:
            self._submit_threaded(job_id)

    def _submit_threaded(self, job_id: str) -> None:
        """Submit job using threading (development mode)."""
        logger.debug(f"Starting threaded execution for job {job_id}")

        # Import here to get fresh app context
        from flask import current_app
        app = current_app._get_current_object()

        def run_job():
            logger.info(f"[Job {job_id}] Thread started")

            # Create application context for this thread
            with app.app_context():
                try:
                    logger.debug(f"[Job {job_id}] Importing SimulationService...")
                    from .simulation_service import SimulationService

                    logger.debug(f"[Job {job_id}] Creating service instance...")
                    service = SimulationService()

                    logger.info(f"[Job {job_id}] Starting simulation...")
                    result = service.run_simulation(
                        job_id,
                        progress_callback=self._create_progress_callback(job_id)
                    )

                    logger.info(f"[Job {job_id}] Simulation completed successfully")
                    logger.debug(f"[Job {job_id}] Result: {result}")

                except Exception as e:
                    logger.error(f"[Job {job_id}] Simulation failed: {str(e)}")
                    logger.error(f"[Job {job_id}] Traceback:\n{traceback.format_exc()}")
                    self._mark_job_failed(job_id, str(e))
                finally:
                    # Clean up
                    if job_id in self._active_jobs:
                        del self._active_jobs[job_id]
                        logger.debug(f"[Job {job_id}] Removed from active jobs")

        thread = threading.Thread(target=run_job, daemon=True, name=f"job-{job_id[:8]}")
        self._active_jobs[job_id] = thread
        thread.start()

        logger.info(f"Job {job_id} submitted, thread {thread.name} started")

    def _submit_celery(self, job_id: str) -> None:
        """Submit job using Celery (production mode)."""
        logger.info(f"Submitting job {job_id} to Celery")
        # Import here to avoid circular imports
        from .tasks import run_simulation_task
        run_simulation_task.delay(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job to cancel.

        Returns:
            True if job was cancelled, False otherwise.
        """
        logger.info(f"Attempting to cancel job {job_id}")

        if job_id in self._active_jobs:
            del self._active_jobs[job_id]
            logger.info(f"Job {job_id} cancelled")
            return True

        logger.warning(f"Job {job_id} not found in active jobs")
        return False

    def _create_progress_callback(self, job_id: str) -> Callable:
        """Create a callback function for progress updates."""
        def callback(progress: int, message: str, energy: Optional[float] = None):
            logger.debug(f"[Job {job_id}] Progress: {progress}% - {message}")
            self._update_job_progress(job_id, progress, message, energy)
        return callback

    def _update_job_progress(
        self,
        job_id: str,
        progress: int,
        message: str,
        current_energy: Optional[float] = None
    ) -> None:
        """Update job progress in database and emit WebSocket event."""
        try:
            job = SimulationJob.query.get(job_id)
            if job:
                job.progress = progress
                job.current_step = message
                db.session.commit()

                logger.debug(f"[Job {job_id}] Updated progress in database")

                # Emit WebSocket update
                update_data = {
                    'job_id': job_id,
                    'progress': progress,
                    'message': message,
                    'current_energy': current_energy,
                    'status': job.status
                }
                socketio.emit(f'job_update_{job_id}', update_data)
                logger.debug(f"[Job {job_id}] Emitted WebSocket update")
            else:
                logger.warning(f"[Job {job_id}] Job not found for progress update")

        except Exception as e:
            logger.error(f"[Job {job_id}] Failed to update progress: {e}")
            logger.error(traceback.format_exc())

    def _mark_job_failed(self, job_id: str, error_message: str) -> None:
        """Mark a job as failed."""
        logger.error(f"[Job {job_id}] Marking as failed: {error_message}")

        try:
            job = SimulationJob.query.get(job_id)
            if job:
                job.status = JobStatus.FAILED.value
                job.error_message = error_message
                job.completed_at = datetime.utcnow()
                db.session.commit()

                logger.info(f"[Job {job_id}] Status updated to FAILED in database")

                socketio.emit(f'job_update_{job_id}', {
                    'job_id': job_id,
                    'status': JobStatus.FAILED.value,
                    'error': error_message
                })
            else:
                logger.error(f"[Job {job_id}] Job not found when trying to mark as failed")

        except Exception as e:
            logger.error(f"[Job {job_id}] Failed to mark job as failed: {e}")
            logger.error(traceback.format_exc())

    def get_active_jobs(self) -> dict:
        """Get currently active jobs for debugging."""
        return {
            job_id: {
                'thread_name': thread.name,
                'is_alive': thread.is_alive()
            }
            for job_id, thread in self._active_jobs.items()
        }