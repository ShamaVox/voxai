import pytest
from server.src.database import Account, db
from server.app import app as flask_app

@pytest.fixture
def client(init_database):
    with flask_app.test_client() as client:
        yield client

@pytest.fixture(scope='function') 
def init_database():
    with flask_app.app_context():
        # Configure the database with a test database
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://ubuntu:voxai@localhost:5432/voxai_db_test"
        db.drop_all()  # Clean up after tests
        db.session.commit()
        db.create_all()  # Create tables
        yield db