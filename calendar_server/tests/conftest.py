import os
import sys
import json
import pytest
from unittest.mock import MagicMock, patch

# Ensure the app root directory is in the path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
# Ensure hex parent is discoverable if recall source is there
hex_parent = os.path.dirname(project_root)
if hex_parent not in sys.path:
    sys.path.insert(0, hex_parent)


# --- Mock Environment Variables ---
# Set default environment variables for tests BEFORE importing app modules
# These can be overridden by a .env file if pytest-dotenv is used, or per test
os.environ.setdefault('RECALL_API_KEY', 'test_recall_key')
os.environ.setdefault('S3_BUCKET', 'test-bucket')
os.environ.setdefault('FLASK_ENV', 'testing') # Ensure testing environment

# Now import the app and other modules AFTER setting env vars
from app import app as flask_app
import config
import data_manager
import recall_adapter
import media_processing
import oauth

# --- Fixtures ---

@pytest.fixture(scope='session')
def app():
    """Session-wide test Flask application."""
    flask_app.config.update({
        "TESTING": True,
        # Add other test-specific configurations if needed
        # e.g., disable CSRF protection for forms if testing directly
        # "WTF_CSRF_ENABLED": False,
    })
    # TODO: Setup/teardown if needed (e.g., initializing a test database)
    yield flask_app
    # TODO: Cleanup after tests if needed

@pytest.fixture()
def client(app):
    """Test client for making requests to the Flask app."""
    return app.test_client()

@pytest.fixture()
def runner(app):
    """Test CLI runner for invoking Flask CLI commands."""
    return app.test_cli_runner()

@pytest.fixture(autouse=True)
def temp_folders(tmp_path, monkeypatch):
    """
    Creates temporary folders for data, tokens, temp and patches config.
    Applied automatically to all tests due to autouse=True.
    """
    d_path = tmp_path / "data"
    t_path = tmp_path / "tokens"
    tmp_data_path = d_path / "temp"

    d_path.mkdir()
    t_path.mkdir()
    tmp_data_path.mkdir()

    # Use monkeypatch to redirect config variables to temp paths
    monkeypatch.setattr(config, 'DATA_FOLDER', str(d_path))
    monkeypatch.setattr(config, 'TOKENS_FOLDER', str(t_path))
    monkeypatch.setattr(config, 'TEMP_FOLDER', str(tmp_data_path))

    # Also patch data_manager paths just in case they were imported directly elsewhere
    monkeypatch.setattr(data_manager, 'DATA_FOLDER', str(d_path))
    monkeypatch.setattr(data_manager, 'TOKENS_FOLDER', str(t_path))

    # Patch media_processing temp folder path
    monkeypatch.setattr(media_processing, 'TEMP_FOLDER', str(tmp_data_path))

    # Patch recall_adapter temp folder path
    monkeypatch.setattr(recall_adapter, 'TEMP_FOLDER', str(tmp_data_path))


    # Create a dummy client_secret.json if needed for OAuthConfig loading
    secrets_file = tmp_path / "client_secret.json"
    dummy_secrets = {
        "web": {
            "client_id": "test_client_id.apps.googleusercontent.com",
            "project_id": "test-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "test_client_secret",
            "redirect_uris": [
                "http://localhost:8080/auth/google/callback",
                "https://your-production-domain.com/auth/google/callback"
             ],
             "javascript_origins": [
                 "http://localhost:8080",
                 "https://your-production-domain.com"
             ]
        }
    }
    with open(secrets_file, 'w') as f:
        json.dump(dummy_secrets, f)
    monkeypatch.setattr(config, 'SECRETS_PATH', str(secrets_file))
    # Reload the OAUTH_CONFIG in config module after patching the path
    monkeypatch.setattr(config, 'OAUTH_CONFIG', config.load_oauth_config())
    # Also patch it in the oauth module if it was imported directly
    monkeypatch.setattr(oauth, 'OAUTH_CONFIG', config.OAUTH_CONFIG)

    yield # Test runs here

    # Cleanup is handled automatically by tmp_path


@pytest.fixture
def mock_recall_api(mocker):
    """Mocks the global RecallAPI instance used in recall_adapter."""
    mock_api = MagicMock(spec=recall_adapter.RecallAPI)
    # Configure default return values for mocked methods
    mock_api.get_headers.return_value = {'Authorization': 'Token test_recall_key'}
    mock_api.handle_response = lambda r: (r.json(), r.status_code) # Simple passthrough mock
    mock_api.create_calendar.return_value = ({"id": "cal_12345"}, 201)
    mock_api.list_finished_bots.return_value = {} # Default to no finished bots
    mock_api.check_bot_status.return_value = (None, 404) # Default to bot not found
    # Mock the download function imported separately
    mocker.patch('recall_adapter.recall_download_video', return_value=(None, [])) # Default fail

    # Patch the global instance in the recall_adapter module
    mocker.patch('recall_adapter.recall_api', new=mock_api)
    return mock_api

@pytest.fixture
def mock_boto3_s3(mocker):
    """Mocks boto3 S3 client interactions."""
    mock_s3_client = MagicMock()
    mock_s3_client.upload_file.return_value = None # Successful upload returns None
    # Mock list_objects_v2 to simulate file not found by default
    mock_s3_client.list_objects_v2.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

    # Patch boto3.client to return our mock S3 client
    mocker.patch('boto3.client', return_value=mock_s3_client)
    return mock_s3_client

@pytest.fixture
def mock_subprocess(mocker):
    """Mocks subprocess.Popen used for ffmpeg."""
    mock_proc = MagicMock()
    mock_proc.communicate.return_value = (b'stdout', b'stderr')
    mock_proc.returncode = 0 # Simulate success by default
    mock_popen = mocker.patch('subprocess.Popen', return_value=mock_proc)
    return mock_popen, mock_proc # Return both Popen mock and the process mock
