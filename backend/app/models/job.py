"""
Database models for simulation jobs.

Provides persistence for tracking simulation jobs,
their status, and results.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import json

from ..extensions import db


class JobStatus(Enum):
    """Possible states for a simulation job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationJob(db.Model):
    """
    Model for tracking quantum chemistry simulation jobs.

    Attributes:
        id: Unique job identifier.
        status: Current job status.
        method: Simulation method (vqe/sqd).
        molecule_name: User-provided molecule name.
        created_at: Job creation timestamp.
        started_at: When job execution began.
        completed_at: When job finished.
        progress: Current progress percentage (0-100).
        result_energy: Final computed energy.
        result_data: Full result data as JSON.
        error_message: Error details if job failed.
        config_data: Simulation configuration as JSON.
    """

    __tablename__ = 'simulation_jobs'

    id = db.Column(db.String(36), primary_key=True)
    status = db.Column(db.String(20), default=JobStatus.PENDING.value, nullable=False)
    method = db.Column(db.String(10), nullable=False)
    molecule_name = db.Column(db.String(100), default="")

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    # Progress tracking
    progress = db.Column(db.Integer, default=0)
    current_step = db.Column(db.String(200), default="")

    # Results
    result_energy = db.Column(db.Float)
    _result_data = db.Column('result_data', db.Text)
    _energy_history = db.Column('energy_history', db.Text)

    # Error tracking
    error_message = db.Column(db.Text)

    # Configuration
    _config_data = db.Column('config_data', db.Text)
    _molecule_data = db.Column('molecule_data', db.Text)

    @property
    def result_data(self) -> Optional[Dict[str, Any]]:
        """Get result data as dictionary."""
        if self._result_data:
            return json.loads(self._result_data)
        return None

    @result_data.setter
    def result_data(self, value: Dict[str, Any]) -> None:
        """Set result data from dictionary."""
        self._result_data = json.dumps(value) if value else None

    @property
    def energy_history(self) -> Optional[list]:
        """Get energy history as list."""
        if self._energy_history:
            return json.loads(self._energy_history)
        return None

    @energy_history.setter
    def energy_history(self, value: list) -> None:
        """Set energy history from list."""
        self._energy_history = json.dumps(value) if value else None

    @property
    def config_data(self) -> Optional[Dict[str, Any]]:
        """Get configuration as dictionary."""
        if self._config_data:
            return json.loads(self._config_data)
        return None

    @config_data.setter
    def config_data(self, value: Dict[str, Any]) -> None:
        """Set configuration from dictionary."""
        self._config_data = json.dumps(value) if value else None

    @property
    def molecule_data(self) -> Optional[Dict[str, Any]]:
        """Get molecule data as dictionary."""
        if self._molecule_data:
            return json.loads(self._molecule_data)
        return None

    @molecule_data.setter
    def molecule_data(self, value: Dict[str, Any]) -> None:
        """Set molecule data from dictionary."""
        self._molecule_data = json.dumps(value) if value else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for API response."""
        return {
            'id': self.id,
            'status': self.status,
            'method': self.method,
            'molecule_name': self.molecule_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'current_step': self.current_step,
            'result_energy': self.result_energy,
            'energy_history': self.energy_history,
            'error_message': self.error_message,
        }

    def __repr__(self) -> str:
        return f"<SimulationJob {self.id} [{self.status}]>"