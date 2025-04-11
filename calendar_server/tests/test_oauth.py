import os
import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

import oauth # Import the module to test
import data_manager
# Get patched paths/config, convert TOKENS_FOLDER back to Path if needed
from config import OAUTH_CONFIG, TOKENS_FOLDER as TOKENS_FOLDER_STR
from pathlib import Path
TOKENS_FOLDER = Path(TOKENS_FOLDER_STR)


# Use fixtures from conftest.py: app, client, temp_folders

@pytest.fixture
def mock_google_creds(mocker):
    """Fixture to mock google.oauth2.credentials.Credentials."""
    mock_creds = MagicMock(spec=Credentials)
    mock_creds.token = "current_access_token"
    mock_creds.refresh_token = "current_refresh_token"
    mock_creds.client_id = OAUTH_CONFIG['client_id']
    mock_creds.client_secret = OAUTH_CONFIG['client_secret']
    mock_creds.token_uri = OAUTH_CONFIG['token_uri']
    mock_creds.scopes = ['scope1']
    mock_creds.expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_creds.valid = True # Initially valid

    # Mock the refresh method
    def refresh_side_effect(*args, **kwargs):
        # Simulate token refresh: update token and expiry
        mock_creds.token = "refreshed_access_token"
        mock_creds.expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        # Sometimes refresh might return a new refresh token
        # mock_creds.refresh_token = "new_refresh_token"
        mock_creds.valid = True

    mock_creds.refresh = MagicMock(side_effect=refresh_side_effect)

    # Patch the Credentials class in the oauth module
    mocker.patch('oauth.Credentials', return_value=mock_creds)
    return mock_creds

@pytest.fixture
def mock_google_flow(mocker):
    """Fixture to mock google_auth_oauthlib.flow.Flow."""
    mock_flow_instance = MagicMock(spec=Flow)
    mock_flow_instance.authorization_url.return_value = ("https://google.com/auth?state=test_state", "test_state")

    # Mock credentials object returned by fetch_token
    mock_creds = MagicMock(spec=Credentials)
    mock_creds.token = "fetched_access_token"
    mock_creds.refresh_token = "fetched_refresh_token"
    mock_creds.client_id = OAUTH_CONFIG['client_id']
    mock_creds.client_secret = OAUTH_CONFIG['client_secret']
    mock_creds.token_uri = OAUTH_CONFIG['token_uri']
    mock_creds.scopes = ['scope1', 'openid', 'email']
    mock_creds.expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_flow_instance.credentials = mock_creds

    mock_flow_instance.fetch_token = MagicMock() # Does not need specific return, sets .credentials

    # Patch Flow.from_client_config to return our instance
    mocker.patch('oauth.Flow.from_client_config', return_value=mock_flow_instance)
    return mock_flow_instance


# --- Test refresh_token_if_needed ---

def test_refresh_token_not_needed(temp_folders, mock_google_creds):
    user_id = "user_valid"
    initial_token_data = {
        "token": "access", "refresh_token": "refresh",
        "client_id": "id", "client_secret": "secret",
        "token_uri": "uri", "scopes": ["s"], "expiry": "2099-01-01T00:00:00Z"
    }
    data_manager.save_token_data(user_id, initial_token_data)

    mock_google_creds.valid = True # Ensure mock says valid
    creds = oauth.refresh_token_if_needed(user_id)

    assert creds is not None
    assert creds.token == "current_access_token" # From mock_google_creds instance
    mock_google_creds.refresh.assert_not_called()

def test_refresh_token_needed_success(temp_folders, mock_google_creds, mocker):
    user_id = "user_expired"
    initial_token_data = {
        "token": "expired_access", "refresh_token": "refresh",
        "client_id": OAUTH_CONFIG['client_id'], "client_secret": OAUTH_CONFIG['client_secret'],
        "token_uri": OAUTH_CONFIG['token_uri'], "scopes": ["s"],
        "expiry": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat() + 'Z'
    }
    data_manager.save_token_data(user_id, initial_token_data)

    mock_google_creds.valid = False # Ensure mock says invalid initially
    mock_save = mocker.spy(data_manager, 'save_token_data')

    creds = oauth.refresh_token_if_needed(user_id)

    assert creds is not None
    mock_google_creds.refresh.assert_called_once()
    assert creds.token == "refreshed_access_token" # Check token was updated by mock refresh

    # Check that token data was saved
    mock_save.assert_called_once()
    saved_data = data_manager.load_token_data(f"{user_id}.json")
    assert saved_data['token'] == "refreshed_access_token"
    assert 'expiry' in saved_data # Expiry should be updated

def test_refresh_token_no_refresh_token(temp_folders, mock_google_creds):
    user_id = "user_no_refresh"
    initial_token_data = {
        "token": "access", "refresh_token": None, # Missing refresh token
         "client_id": "id", "client_secret": "secret", "token_uri": "uri", "scopes": ["s"]
    }
    data_manager.save_token_data(user_id, initial_token_data)

    mock_google_creds.valid = False
    mock_google_creds.refresh_token = None # Ensure mock creds also lacks refresh token

    creds = oauth.refresh_token_if_needed(user_id)
    assert creds is None
    mock_google_creds.refresh.assert_not_called()

def test_refresh_token_missing_fields(temp_folders):
    user_id = "user_missing_fields"
    initial_token_data = {
        "token": "access", "refresh_token": "refresh"
        # Missing client_id, secret, etc.
    }
    data_manager.save_token_data(user_id, initial_token_data)
    creds = oauth.refresh_token_if_needed(user_id)
    assert creds is None

def test_refresh_token_refresh_failure(temp_folders, mock_google_creds, mocker):
    user_id = "user_refresh_fail"
    initial_token_data = {
        "token": "expired", "refresh_token": "refresh",
        "client_id": OAUTH_CONFIG['client_id'], "client_secret": OAUTH_CONFIG['client_secret'],
        "token_uri": OAUTH_CONFIG['token_uri'], "scopes": ["s"],
        "expiry": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat() + 'Z'
    }
    data_manager.save_token_data(user_id, initial_token_data)

    mock_google_creds.valid = False
    # Simulate a refresh exception (e.g., invalid grant)
    mock_google_creds.refresh.side_effect = Exception("invalid_grant: Token has been expired or revoked.")

    mock_save = mocker.spy(data_manager, 'save_token_data')

    creds = oauth.refresh_token_if_needed(user_id)

    assert creds is None
    mock_google_creds.refresh.assert_called_once()
    mock_save.assert_not_called() # Should not save on failure

# --- Test get_user_info ---

def test_get_user_info_success(mocker):
    mock_creds = MagicMock(spec=Credentials)
    mock_creds.token = "valid_token"
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 200
    user_info_payload = {"id": "12345", "email": "test@example.com", "name": "Test User"}
    mock_response.json.return_value = user_info_payload
    mock_response.raise_for_status = MagicMock() # No exception on 200

    mocker.patch('requests.get', return_value=mock_response)

    user_info = oauth.get_user_info(mock_creds)

    requests.get.assert_called_once_with(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': 'Bearer valid_token'}
    )
    assert user_info == user_info_payload

def test_get_user_info_request_error(mocker):
    mock_creds = MagicMock(spec=Credentials)
    mock_creds.token = "valid_token"
    # Simulate a requests exception
    mocker.patch('requests.get', side_effect=requests.exceptions.Timeout("Connection timed out"))

    user_info = oauth.get_user_info(mock_creds)
    assert user_info is None

def test_get_user_info_http_error(mocker):
    mock_creds = MagicMock(spec=Credentials)
    mock_creds.token = "invalid_token"
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    # Simulate raise_for_status raising an HTTPError
    mock_response.raise_for_status = MagicMock(side_effect=requests.exceptions.HTTPError("Unauthorized", response=mock_response))

    mocker.patch('requests.get', return_value=mock_response)

    user_info = oauth.get_user_info(mock_creds)
    assert user_info is None

def test_get_user_info_missing_id_and_email(mocker):
    mock_creds = MagicMock(spec=Credentials)
    mock_creds.token = "valid_token"
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 200
    user_info_payload = {"name": "Test User Only"} # Missing id and email
    mock_response.json.return_value = user_info_payload
    mock_response.raise_for_status = MagicMock()

    mocker.patch('requests.get', return_value=mock_response)

    user_info = oauth.get_user_info(mock_creds)
    assert user_info is None # Treat as failure if no identifier

# --- Test Flask Routes ---

def test_google_auth_route(client, mock_google_flow):
    """Test the redirect to Google's authorization URL."""
    response = client.get('/auth/google')
    assert response.status_code == 302 # Redirect status
    # Check that the location header matches the mocked authorization URL
    assert response.location == "https://google.com/auth?state=test_state"
    # Check if the flow was initialized correctly
    # Access the mocked class directly for assertion
    flow_mock = oauth.Flow.from_client_config # The mock object itself
    flow_mock.assert_called_once()
    mock_google_flow.authorization_url.assert_called_once_with(
        access_type='offline', prompt='consent'
    )

def test_google_callback_route_success(client, mock_google_flow, mocker):
    """Test successful callback handling."""
    user_id = "test@example.com"
    mock_user_info = {"id": "google_id_123", "email": user_id}
    mock_get_user_info = mocker.patch('oauth.get_user_info', return_value=mock_user_info)
    # Mock the calendar processing function it tries to call
    # Correct the patch target: it's imported into oauth from calendar_processing
    mock_process_calendar = mocker.patch('calendar_processing.process_user_calendar', return_value=True)
    mock_save_token = mocker.spy(data_manager, 'save_token_data')

    auth_code = "test_auth_code"
    response = client.get(f'/auth/google/callback?code={auth_code}')

    assert response.status_code == 200
    assert b"Authentication successful!" in response.data

    # Verify flow usage
    mock_google_flow.fetch_token.assert_called_once_with(code=auth_code)
    mock_get_user_info.assert_called_once_with(mock_google_flow.credentials)

    # Verify token saving
    mock_save_token.assert_called_once()
    args, kwargs = mock_save_token.call_args
    saved_user_id, saved_token_data = args
    assert saved_user_id == user_id
    assert saved_token_data['token'] == 'fetched_access_token'
    assert saved_token_data['refresh_token'] == 'fetched_refresh_token'

    # Verify initial calendar processing trigger
    mock_process_calendar.assert_called_once_with(user_id, saved_token_data)

def test_google_callback_route_no_code(client):
    """Test callback when no authorization code is provided."""
    response = client.get('/auth/google/callback') # No code query param
    assert response.status_code == 400
    assert b"Authorization failed" in response.data

def test_google_callback_route_fetch_token_error(client, mock_google_flow):
    """Test callback when fetching token fails."""
    mock_google_flow.fetch_token.side_effect = Exception("Failed to fetch token")
    auth_code = "test_auth_code"
    response = client.get(f'/auth/google/callback?code={auth_code}')
    assert response.status_code == 500
    assert b"An internal error occurred during authentication" in response.data

def test_google_callback_route_get_user_info_error(client, mock_google_flow, mocker):
    """Test callback when fetching user info fails."""
    mocker.patch('oauth.get_user_info', return_value=None) # Simulate failure
    auth_code = "test_auth_code"
    response = client.get(f'/auth/google/callback?code={auth_code}')
    assert response.status_code == 500
    assert b"Could not retrieve user information" in response.data

def test_google_callback_route_process_calendar_error(client, mock_google_flow, mocker):
    """Test callback succeeds even if initial calendar processing fails."""
    user_id = "test@example.com"
    mock_user_info = {"id": "google_id_123", "email": user_id}
    mocker.patch('oauth.get_user_info', return_value=mock_user_info)
    # Simulate error during calendar processing
    # Correct the patch target
    mock_process_calendar = mocker.patch('calendar_processing.process_user_calendar', side_effect=Exception("Sync Error"))
    mock_save_token = mocker.spy(data_manager, 'save_token_data')

    auth_code = "test_auth_code"
    response = client.get(f'/auth/google/callback?code={auth_code}')

    # Auth itself should still be considered successful
    assert response.status_code == 200
    assert b"Authentication successful!" in response.data

    # Verify token saving still happened
    mock_save_token.assert_called_once()
    # Verify initial calendar processing was attempted
    mock_process_calendar.assert_called_once()
