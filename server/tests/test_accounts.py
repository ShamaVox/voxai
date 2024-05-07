import pytest
from server.src.database import Account, db
from server.app import app as flask_app

def test_account_repr(init_database):
    """Test the __repr__ method of the Account model."""
    account = Account(email="test@example.com")
    assert repr(account) == "<Account test@example.com>"

def test_default_values(init_database):
    """Test if default values are set correctly for new accounts."""
    account = Account(email="test2@example.com")
    db.session.add(account)
    db.session.commit()

    retrieved_account = Account.query.filter_by(email="test2@example.com").first()
    assert retrieved_account.name == "Default Name"
    assert retrieved_account.account_type == "Recruiter"
    assert retrieved_account.organization == "Default Company"

def test_account_query_by_email(init_database):
    """Test querying for an account by email."""
    account = Account(email="test3@example.com", name="Query Test")
    db.session.add(account)
    db.session.commit()

    found_account = Account.query.filter_by(email="test3@example.com").first()
    assert found_account is not None
    assert found_account.name == "Query Test"

def test_account_creation(init_database):
    """Test account creation with valid data."""
    with flask_app.app_context():
        account = Account(email="test4@example.com", name="Test User")
        db.session.add(account)
        db.session.commit()

        retrieved_account = Account.query.filter_by(email="test4@example.com").first()
        assert retrieved_account is not None
        assert retrieved_account.name == "Test User"