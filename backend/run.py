"""
Application entry point for development.

Run with: python run.py
"""

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🔬 Quantum Chemistry API Server")
    print("=" * 60)
    print(f"🌐 API URL: http://localhost:5000/api/v1")
    print(f"📊 Debug Status: http://localhost:5000/debug/status")
    print(f"❤️  Health Check: http://localhost:5000/health")
    print("=" * 60 + "\n")

    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True,
        log_output=True
    )