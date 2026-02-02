"""
API error handlers and custom exceptions.

Provides consistent error responses across all endpoints.
"""

from flask import Flask, jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException


class APIError(Exception):
    """Base class for API errors."""

    def __init__(self, message: str, status_code: int = 400, payload: dict = None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self) -> dict:
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv


class JobNotFoundError(APIError):
    """Raised when a job is not found."""

    def __init__(self, job_id: str):
        super().__init__(
            message=f"Job not found: {job_id}",
            status_code=404
        )


class InvalidMoleculeError(APIError):
    """Raised when molecule definition is invalid."""

    def __init__(self, message: str):
        super().__init__(
            message=f"Invalid molecule: {message}",
            status_code=400
        )


class SimulationError(APIError):
    """Raised when simulation fails."""

    def __init__(self, message: str):
        super().__init__(
            message=f"Simulation error: {message}",
            status_code=500
        )


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""

    def __init__(self):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            status_code=429
        )


def register_error_handlers(app: Flask) -> None:
    """Register error handlers with Flask app."""

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        return jsonify({
            'error': 'Validation error',
            'status_code': 400,
            'details': error.messages
        }), 400

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        return jsonify({
            'error': error.description,
            'status_code': error.code
        }), error.code

    @app.errorhandler(Exception)
    def handle_generic_exception(error: Exception):
        app.logger.error(f"Unhandled exception: {error}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'status_code': 500
        }), 500