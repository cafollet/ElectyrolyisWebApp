"""
Simulation execution service.

Bridges the Flask API with the quantum chemistry package.
"""

from datetime import datetime
from typing import Optional, Callable, Dict, Any
import time
import traceback

from ..extensions import db, socketio
from ..models.job import SimulationJob, JobStatus
from ..utils.molecule_builder import MoleculeBuilder
from ..logging_config import get_logger

logger = get_logger('app.simulation')


class SimulationService:
    """
    Service for executing quantum chemistry simulations.

    Integrates with the quantum_chemistry package to run
    VQE and SQD simulations.
    """

    def __init__(self):
        logger.debug("SimulationService initialized")
        self.molecule_builder = MoleculeBuilder()

    def run_simulation(
        self,
        job_id: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a simulation job.

        Args:
            job_id: Unique job identifier.
            progress_callback: Optional callback for progress updates.

        Returns:
            Dictionary containing simulation results.
        """
        logger.info(f"[Job {job_id}] Starting simulation execution")

        job = SimulationJob.query.get(job_id)

        if not job:
            logger.error(f"[Job {job_id}] Job not found in database")
            raise ValueError(f"Job not found: {job_id}")

        logger.info(f"[Job {job_id}] Found job: method={job.method}, molecule={job.molecule_name}")
        logger.debug(f"[Job {job_id}] Molecule data: {job.molecule_data}")
        logger.debug(f"[Job {job_id}] Config data: {job.config_data}")

        # Update job status to running
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        db.session.commit()
        logger.info(f"[Job {job_id}] Status updated to RUNNING")

        start_time = time.time()

        try:
            # Build molecule
            if progress_callback:
                progress_callback(5, "Building molecule...")

            logger.debug(f"[Job {job_id}] Building molecule from data...")
            molecule_data = job.molecule_data

            # Determine if we need PySCF molecule (for SQD) or PennyLane (for VQE)
            use_pyscf = job.method == 'sqd'
            logger.debug(f"[Job {job_id}] Using PySCF: {use_pyscf}")

            molecule = self.molecule_builder.build(molecule_data, for_sqd=use_pyscf)
            logger.info(f"[Job {job_id}] Molecule built successfully")

            # Import quantum chemistry package
            if progress_callback:
                progress_callback(10, "Loading quantum chemistry modules...")

            logger.debug(f"[Job {job_id}] Importing quantum_chemistry package...")

            try:
                # Enable JAX 64-bit precision
                import jax
                jax.config.update("jax_enable_x64", True)
                logger.debug(f"[Job {job_id}] JAX 64-bit precision enabled")

                from quantum_chemistry import (
                    GroundStateSimulator,
                    VQEConfig,
                    SQDConfig,
                )
                logger.info(f"[Job {job_id}] Quantum chemistry modules imported successfully")

            except ImportError as e:
                logger.error(f"[Job {job_id}] Failed to import quantum_chemistry: {e}")
                logger.error(traceback.format_exc())
                raise RuntimeError(f"Failed to import quantum chemistry package: {e}")

            # Create simulator
            logger.debug(f"[Job {job_id}] Creating GroundStateSimulator...")

            # For SQD with hardware mode, extract the API key (not persisted)
            ibm_api_key = None
            if job.method == 'sqd':
                sqd_cfg = job.config_data.get('sqd_config', {})
                if sqd_cfg.get('use_hardware'):
                    ibm_api_key = sqd_cfg.get('ibm_api_key')
                    if ibm_api_key:
                        logger.info(f"[Job {job_id}] IBM Quantum hardware mode enabled")
                    else:
                        logger.warning(f"[Job {job_id}] Hardware mode requested but no API key provided")
                else:
                    logger.info(f"[Job {job_id}] SQD running in local simulation mode (Qiskit Aer)")

            simulator = GroundStateSimulator(ibm_api_key=ibm_api_key)

            # Configure based on method
            if job.method == 'vqe':
                logger.info(f"[Job {job_id}] Running VQE simulation")
                result = self._run_vqe(
                    simulator,
                    molecule,
                    job.config_data.get('vqe_config', {}),
                    job.molecule_data.get('name', ''),
                    progress_callback,
                    job_id
                )
            else:  # sqd
                logger.info(f"[Job {job_id}] Running SQD simulation")
                result = self._run_sqd(
                    simulator,
                    molecule,
                    job.config_data.get('sqd_config', {}),
                    job.molecule_data.get('name', ''),
                    progress_callback,
                    job_id
                )

            # Update job with results
            execution_time = time.time() - start_time
            logger.info(f"[Job {job_id}] Simulation completed in {execution_time:.2f}s")
            logger.info(f"[Job {job_id}] Final energy: {result.energy}")

            job.status = JobStatus.COMPLETED.value
            job.completed_at = datetime.utcnow()
            job.progress = 100
            job.result_energy = float(result.energy)
            job.energy_history = [float(e) for e in result.energy_history] if result.energy_history else []
            job.result_data = {
                'energy_hartree': float(result.energy),
                'energy_ev': float(result.energy) * 27.2114,
                'mapping': result.mapping.value if result.mapping else None,
                'converged': result.converged,
                'num_iterations': result.num_iterations,
                'execution_time_seconds': execution_time,
                'metadata': result.metadata if hasattr(result, 'metadata') else {}
            }

            db.session.commit()
            logger.info(f"[Job {job_id}] Results saved to database")

            if progress_callback:
                progress_callback(100, "Simulation complete!", result.energy)

            return job.result_data

        except Exception as e:
            logger.error(f"[Job {job_id}] Simulation failed: {str(e)}")
            logger.error(f"[Job {job_id}] Full traceback:\n{traceback.format_exc()}")

            job.status = JobStatus.FAILED.value
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            db.session.commit()

            raise

    def _run_vqe(
        self,
        simulator,
        molecule,
        config_dict: Dict[str, Any],
        name: str,
        progress_callback: Optional[Callable],
        job_id: str
    ):
        """Run VQE simulation with progress tracking."""
        from quantum_chemistry import VQEConfig

        logger.debug(f"[Job {job_id}] VQE config: {config_dict}")

        config = VQEConfig(
            step_size=config_dict.get('step_size', 0.2),
            num_steps=config_dict.get('num_steps', 200),
            convergence_threshold=config_dict.get('convergence_threshold')
        )

        logger.info(f"[Job {job_id}] VQE Config: step_size={config.step_size}, num_steps={config.num_steps}")

        if progress_callback:
            progress_callback(15, f"Starting VQE optimization ({config.num_steps} steps)...")

        # Run simulation
        logger.debug(f"[Job {job_id}] Calling simulator.run() with VQE...")
        result = simulator.run(
            molecule,
            method='vqe',
            name=name,
            vqe_config=config
        )

        logger.debug(f"[Job {job_id}] VQE completed, result: {result}")
        return result

    def _run_sqd(
        self,
        simulator,
        molecule,
        config_dict: Dict[str, Any],
        name: str,
        progress_callback: Optional[Callable],
        job_id: str
    ):
        """Run SQD simulation with progress tracking."""
        from quantum_chemistry import SQDConfig

        logger.debug(f"[Job {job_id}] SQD config: {config_dict}")

        config = SQDConfig(
            samples_per_batch=config_dict.get('samples_per_batch', 500),
            max_iterations=config_dict.get('max_iterations', 100),
            num_batches=config_dict.get('num_batches', 5),
            num_shots=config_dict.get('num_shots', 10000)
        )

        logger.info(f"[Job {job_id}] SQD Config: samples={config.samples_per_batch}, iterations={config.max_iterations}")

        if progress_callback:
            progress_callback(15, "Running quantum circuit...")

        # Run simulation
        logger.debug(f"[Job {job_id}] Calling simulator.run() with SQD...")
        result = simulator.run(
            molecule,
            method='sqd',
            name=name,
            sqd_config=config
        )

        logger.debug(f"[Job {job_id}] SQD completed, result: {result}")
        return result