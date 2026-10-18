"""WSGI entrypoint for gunicorn.

Usage:
    gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 4 --timeout 120 wsgi:app

Initializes the SQLite database and starts the background traffic recorder
before serving requests. Keep workers at 1 to avoid duplicate recorder threads.
"""

import threading

from app import app, init_db, record_traffic

init_db()
t = threading.Thread(target=record_traffic, daemon=True)
t.start()
