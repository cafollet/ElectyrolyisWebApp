"""
WSGI entry point for production deployment.

Run with: gunicorn -k eventlet -w 1 wsgi:app
"""

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app)