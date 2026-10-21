import pytest
from db import Database
from flask import Flask

def test_database_connection_failure_handling():
    """Verify application handles unreachable MongoDB instance without crashing."""
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb://127.0.0.1:54321/nonexistent_db"
    app.config["MONGO_SERVER_SELECTION_TIMEOUT_MS"] = 500
    app.config["MONGO_CONNECT_TIMEOUT_MS"] = 500
    app.config["TESTING"] = False
    app.config["ENABLE_EMBEDDED_FALLBACK"] = False

    isolated_db = Database()
    # Initializing should catch ServerSelectionTimeoutError and set is_connected = False
    isolated_db.init_app(app)

    assert isolated_db.is_connected is False
    assert isolated_db.connection_error is not None
    assert isolated_db.users is None
    assert isolated_db.appointments is None

def test_mongomock_connection_success():
    """Verify in-memory mongomock initializes cleanly."""
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongomock://localhost/test_db"
    app.config["TESTING"] = True

    mock_db = Database()
    mock_db.init_app(app)

    assert mock_db.is_connected is True
    assert mock_db.is_mock is True
    assert mock_db.users is not None
