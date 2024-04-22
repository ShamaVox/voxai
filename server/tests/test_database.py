import pytest
from server.src.database import Account, db
from server.app import app as flask_app

@pytest.fixture
def client():
    with flask_app.test_client() as client:
        yield client


@pytest.fixture(scope='module')  # Use module scope to avoid creating multiple connections
def init_database():
    with flask_app.app_context():
        # Configure the database with a test database
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://ubuntu:voxai@localhost:5432/voxai_db_test" 
        db.create_all()  # Create tables
        yield db
        db.drop_all()  # Clean up after tests

def test_database_connection(init_database):
    """Test if the database connection is established successfully."""
    with flask_app.app_context():
        assert init_database.engine.connect()

def test_account_creation(init_database):
    """Test account creation with valid data."""
    with flask_app.app_context():
        account = Account(email="test@example.com", name="Test User")
        db.session.add(account)
        db.session.commit()

        retrieved_account = Account.query.filter_by(email="test@example.com").first()
        assert retrieved_account is not None
        assert retrieved_account.name == "Test User"