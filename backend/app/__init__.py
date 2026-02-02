"""
Flask application factory.

Creates and configures the Flask application with all extensions,
blueprints, and error handlers.
"""

import logging
from flask import Flask, jsonify, request, g
from flask_cors import CORS
import time
import uuid

from .config import get_config
from .extensions import db, cors, socketio
from .api import api_bp
from .api.errors import register_error_handlers
from .logging_config import setup_logging, get_logger


def create_app(config_class=None):
    """
    Application factory for creating Flask app instances.

    Args:
        config_class: Configuration class to use. If None, uses environment-based config.

    Returns:
        Configured Flask application instance.
    """
    # Setup logging first
    setup_logging(level="DEBUG", log_file="quantum_api.log")
    logger = get_logger('app')

    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    logger.info(f"Creating app with config: {config_class.__name__}")

    # Initialize extensions
    _init_extensions(app)

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register request hooks for logging
    _register_request_hooks(app)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        logger.debug("Health check requested")
        return jsonify({
            'status': 'healthy',
            'service': 'quantum-chemistry-api'
        })

    # Debug endpoint
    @app.route('/debug/status')
    def debug_status():
        """Debug endpoint to check system status."""
        from .models.job import SimulationJob

        jobs = SimulationJob.query.all()
        job_summary = {}
        for job in jobs:
            status = job.status
            job_summary[status] = job_summary.get(status, 0) + 1

        return jsonify({
            'status': 'ok',
            'database': 'connected',
            'total_jobs': len(jobs),
            'jobs_by_status': job_summary,
        })

    logger.info("Application created successfully")
    return app


def _init_extensions(app: Flask) -> None:
    """Initialize Flask extensions."""
    logger = get_logger('app.extensions')

    logger.debug("Initializing database...")
    db.init_app(app)

    logger.debug("Initializing CORS...")
    cors.init_app(
        app,
        origins=app.config['CORS_ORIGINS'],
        supports_credentials=True
    )

    logger.debug("Initializing SocketIO...")
    socketio.init_app(
        app,
        cors_allowed_origins=app.config['CORS_ORIGINS'],
        async_mode='threading'  # Changed from 'eventlet' for simpler debugging
    )

    # Create database tables
    with app.app_context():
        logger.debug("Creating database tables...")
        db.create_all()
        logger.info("Database initialized")


def _register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    logger = get_logger('app.blueprints')
    logger.debug("Registering API blueprint...")
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    logger.info("Blueprints registered")


def _register_request_hooks(app: Flask) -> None:
    """Register request/response logging hooks."""
    logger = get_logger('app.requests')

    @app.before_request
    def before_request():
        """Log incoming requests and start timer."""
        g.request_id = str(uuid.uuid4())[:8]
        g.start_time = time.time()

        # Log request details
        logger.info(
            f"[{g.request_id}] --> {request.method} {request.path} "
            f"| Client: {request.remote_addr}"
        )

        # Log request body for POST/PUT (but not sensitive data)
        if request.method in ['POST', 'PUT', 'PATCH'] and request.is_json:
            try:
                body = request.get_json()
                # Truncate large bodies
                body_str = str(body)
                if len(body_str) > 500:
                    body_str = body_str[:500] + "... (truncated)"
                logger.debug(f"[{g.request_id}] Request body: {body_str}")
            except Exception:
                pass

    @app.after_request
    def after_request(response):
        """Log response details."""
        duration = (time.time() - g.start_time) * 1000  # Convert to ms

        # Color code by status
        status_code = response.status_code
        if status_code < 300:
            status_indicator = "✓"
        elif status_code < 400:
            status_indicator = "→"
        elif status_code < 500:
            status_indicator = "✗"
        else:
            status_indicator = "!!"

        logger.info(
            f"[{g.request_id}] <-- {status_indicator} {status_code} "
            f"| {duration:.2f}ms"
        )

        return response