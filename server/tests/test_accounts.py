import pytest
from server.src.database import Account, Organization, db
from server.app import app as flask_app
from sqlalchemy.exc import IntegrityError

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
    assert retrieved_account.organization_id is None

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

def test_unique_email_constraint():
    """Test that two accounts cannot have the same email."""
    with flask_app.app_context():
        account1 = Account(email="duplicate@example.com", name="Test User 1")
        db.session.add(account1)
        db.session.commit()

        account2 = Account(email="duplicate@example.com", name="Test User 2")
        db.session.add(account2)
        with pytest.raises(IntegrityError):
            db.session.commit()

def test_account_update(init_database):
    """Test updating an account's information."""
    with flask_app.app_context():
        initial_org = Organization(name="Initial Org")
        db.session.add(initial_org)
        db.session.flush()
        account = Account(email="update@example.com", name="Original Name", organization=initial_org)
        db.session.add(account)
        db.session.commit()


        new_org = Organization.query.filter_by(name="New Company").first()
        if new_org is None:
            new_org = Organization(name="New Company") 
            db.session.add(new_org)
            

        account.name = "Updated Name"
        account.organization = new_org  # Assign the object
        db.session.commit()

        updated_account = Account.query.filter_by(email="update@example.com").first()
        assert updated_account.name == "Updated Name"
        assert updated_account.organization.name == "New Company"  

def test_account_delete():
    """Test deleting an account."""
    with flask_app.app_context():
        account = Account(email="delete@example.com", name="Delete Test")
        db.session.add(account)
        db.session.commit()

        db.session.delete(account)
        db.session.commit()

        deleted_account = Account.query.filter_by(email="delete@example.com").first()
        assert deleted_account is None