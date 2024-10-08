import pytest
from flask import json
from server.src import input_validation, database
from server.src.routes import auth
from server.src.database import db, Account, Organization
from server.app import app as flask_app
from .utils.synthetic_data import create_synthetic_data

@pytest.mark.parametrize(
    "email, expected_message, expected_status_code",
    [
        ("valid@example.com", "Verification code sent successfully", 200),
        ("invalid_email", "Invalid email", 400),
    ],
)
def test_send_code(client, init_database, email, expected_message, expected_status_code, mocker):
    # Mock the necessary functions
    mocker.patch.object(input_validation, "is_valid_email")
    mocker.patch.object(auth, "generate_verification_code")
    mocker.patch.object(auth, "send_verification_code")

    # Set up the mocked return values
    auth.generate_verification_code.return_value = "123456"

    # Send a POST request to the endpoint
    response = client.post("/api/send_code", json={"email": email})

    # Assert the response
    assert response.status_code == expected_status_code
    assert json.loads(response.data)["message"] == expected_message

    # Assert the function calls
    if expected_status_code == 200:
        auth.generate_verification_code.assert_called_once()
        auth.send_verification_code.assert_called_once_with(email, "123456")

        # Check if the account exists in the test database
        with flask_app.app_context():
            account_exists = Account.query.filter_by(email=email).first() is not None
            assert json.loads(response.data)["account_exists"] == account_exists

@pytest.mark.parametrize(
    "email, code, expected_message, expected_status_code",
    [
        ("valid@example.com", "123123", "Verification code is valid", 200),
        ("invalid@example.com", "invalid_code", "Invalid verification code", 401),
    ],
)
def test_validate_code_existing_account(client, init_database, email, code, expected_message, expected_status_code):
    # Create a test account in the database
    with flask_app.app_context():
        org_name = "New Org" 
        org_obj = Organization.query.filter_by(name=org_name).first()
        if org_obj is None:
            org_obj = Organization(name=org_name)
            db.session.add(org_obj) 
            db.session.flush()
        test_account = Account(email=email, name="Test User", organization=org_obj, account_type="Test Type")
        db.session.add(test_account)
        db.session.commit()

    # Send a POST request to the endpoint
    response = client.post("/api/validate_code", json={"email": email, "code": code})

    # Assert the response
    assert response.status_code == expected_status_code
    assert json.loads(response.data)["message"] == expected_message

    if expected_status_code == 200:
        assert json.loads(response.data)["name"] == "Test User"
        assert json.loads(response.data)["account_type"] == "Test Type"
        assert json.loads(response.data)["email"] == email

@pytest.mark.parametrize(
    "email, code, name, organization, account_type, expected_message, expected_status_code",
    [
        ("new@example.com", "123123", "New User", "New Org 1", "New Type", "Account created", 201),
        ("new2@example.com", "123123", None, "New Org 2", "New Type", "A name is needed to create an account", 401),
        ("new3@example.com", "123123", "New User", None, "New Type", "An organization is needed to create an account", 401),
        ("new4@example.com", "123123", "New User", "New Org 3", None, "An account type is needed to create an account", 401),
    ],
)
def test_validate_code_new_account(client, init_database, email, code, name, organization, account_type, expected_message, expected_status_code):
    create_synthetic_data(10)
    # Send a POST request to the endpoint

    response = client.post("/api/validate_code", json={"email": email, "code": code, "name": name, "organization": organization, "accountType": account_type})
    with flask_app.app_context():
        org_obj = Organization.query.filter_by(name=organization).first()

    # Assert the response
    assert json.loads(response.data)["message"] == expected_message
    assert response.status_code == expected_status_code

    if expected_status_code == 201:
        assert json.loads(response.data)["name"] == name
        assert json.loads(response.data)["organization"] == organization
        assert json.loads(response.data)["account_type"] == account_type
        assert json.loads(response.data)["email"] == email

        # Check if the account was created in the test database
        with flask_app.app_context():
            new_account = Account.query.filter_by(email=email).first()
            assert new_account is not None
            assert new_account.name == name
            assert new_account.organization == org_obj
            assert new_account.account_type == account_type