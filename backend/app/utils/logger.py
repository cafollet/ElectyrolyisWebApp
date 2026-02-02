"""
Logging configuration and utilities.

Provides structured logging with different levels for development and production.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json
from flask import has_request_context, request

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


class RequestFormatter(logging.Formatter):
    """Custom formatter that includes request context when available."""

    def format(self, record):
        # Add request context if available
        if has_request_context():
            record.request_id = request.headers.get('X-Request-ID', '-')
            record.method = request.method
            record.path = request.path
            record.ip = request.remote_addr
        else:
            record.request_id = '-'
            record.method = '-'
            record.path = '-'
            record.ip = '-'

        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        log_object = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_object['exception'] = self.formatException(record.exc_info)

        # Add request context if available
        if has_request_context():
            log_object['request'] = {
                'method': request.method,
                'path': request.path,
                'ip': request.remote_addr,
                'request_id': request.headers.get('X-Request-ID'),
            }

        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                           'levelname', 'levelno', 'lineno', 'module', 'exc_info',
                           'exc_text', 'stack_info', 'pathname', 'processName',
                           'relativeCreated', 'thread', 'threadName', 'getMessage']:
                log_object[key] = value

        return json.dumps(log_object)


def setup_logging(app=None, level='INFO', json_format=False):
    """
    Configure logging for the application.

    Args:
        app: Flask app instance (optional)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON formatting for production
    """
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []

    # Set base logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Console handler with color for development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if json_format:
        console_formatter = JSONFormatter()
    else:
        # Colored formatter for development
        console_format = (
            '\033[1m%(asctime)s\033[0m - '
            '\033[94m%(name)s\033[0m - '
            '\033[%(levelcolor)sm%(levelname)s\033[0m - '
            '%(message)s'
        )
        console_formatter = ColoredFormatter(console_format)

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler for all logs
    file_handler = logging.FileHandler(LOGS_DIR / 'app.log')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = RequestFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Error file handler
    error_handler = logging.FileHandler(LOGS_DIR / 'errors.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)

    # Simulation-specific log
    sim_logger = logging.getLogger('simulation')
    sim_handler = logging.FileHandler(LOGS_DIR / 'simulations.log')
    sim_handler.setFormatter(file_formatter)
    sim_logger.addHandler(sim_handler)
    sim_logger.setLevel(logging.DEBUG)

    # Set specific log levels for noisy libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('qiskit').setLevel(logging.WARNING)

    if app:
        app.logger.info(f"Logging configured at {level} level")


class ColoredFormatter(RequestFormatter):
    """Colored formatter for console output."""

    LEVEL_COLORS = {
        'DEBUG': '37',
        'INFO': '32',
        'WARNING': '33',
        'ERROR': '31',
        'CRITICAL': '35',
    }

    def format(self, record):
        record.levelcolor = self.LEVEL_COLORS.get(record.levelname, '37')
        return super().format(record)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name or __name__)


# Convenience logging functions
def log_api_request(logger: logging.Logger, request_data: dict = None):
    """Log API request details."""
    logger.info(
        f"API Request: {request.method} {request.path}",
        extra={
            'request_data': request_data,
            'headers': dict(request.headers),
            'args': dict(request.args),
        }
    )


def log_api_response(logger: logging.Logger, status_code: int, response_data: dict = None):
    """Log API response details."""
    logger.info(
        f"API Response: {status_code}",
        extra={
            'response_data': response_data,
            'status_code': status_code,
        }
    )


def log_simulation_start(logger: logging.Logger, job_id: str, method: str, molecule_name: str):
    """Log simulation start."""
    logger.info(
        f"Starting {method.upper()} simulation for {molecule_name}",
        extra={
            'job_id': job_id,
            'method': method,
            'molecule': molecule_name,
            'event': 'simulation_start'
        }
    )


def log_simulation_progress(logger: logging.Logger, job_id: str, progress: int, message: str):
    """Log simulation progress."""
    logger.debug(
        f"Simulation progress: {progress}% - {message}",
        extra={
            'job_id': job_id,
            'progress': progress,
            'message': message,
            'event': 'simulation_progress'
        }
    )


def log_simulation_complete(logger: logging.Logger, job_id: str, energy: float, time_seconds: float):
    """Log simulation completion."""
    logger.info(
        f"Simulation completed: Energy = {energy} Ha, Time = {time_seconds:.2f}s",
        extra={
            'job_id': job_id,
            'energy': energy,
            'execution_time': time_seconds,
            'event': 'simulation_complete'
        }
    )


def log_simulation_error(logger: logging.Logger, job_id: str, error: Exception):
    """Log simulation error."""
    logger.error(
        f"Simulation failed: {str(error)}",
        extra={
            'job_id': job_id,
            'error_type': type(error).__name__,
            'event': 'simulation_error'
        },
        exc_info=True
    )