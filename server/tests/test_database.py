import pytest
from server.src.database import Account, db
from server.app import app as flask_app

def test_database_connection(init_database):
    """Test if the database connection is established successfully."""
    with flask_app.app_context():
        assert init_database.engine.connect()