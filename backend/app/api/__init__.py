"""
API Blueprint registration.

Consolidates all API routes into a single blueprint.
"""

from flask import Blueprint

api_bp = Blueprint('api', __name__)

from . import routes, simulation, molecules