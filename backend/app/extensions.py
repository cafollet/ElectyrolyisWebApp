"""
Flask extension initialization.

Centralizes all Flask extensions for clean imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO

# Database
db = SQLAlchemy()

# CORS
cors = CORS()

# WebSocket for real-time updates
socketio = SocketIO()