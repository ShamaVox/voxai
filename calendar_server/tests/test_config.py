import os
import json
import pytest
from unittest.mock import patch # Import patch
import config # Import config module

# Use fixture from conftest to handle temp paths and dummy secrets file
def test_load_oauth_config_success(temp_folders):
    """Verify OAuth config loads correctly from the dummy file."""
    # Config is patched by fixture, load_oauth_config uses patched path
    oauth_config = config.load_oauth_config()

    assert oauth_config['client_id'] == "test_client_id.apps.googleusercontent.com"
    assert oauth_config['client_secret'] == "test_client_secret"
    assert oauth_config['token_uri'] == "https://oauth2.googleapis.com/token"
    # Assumes the first redirect URI is used
    assert oauth_config['redirect_uri'] == "http://localhost:8080/auth/google/callback"

def test_load_oauth_config_file_not_found(monkeypatch):
    """Verify behavior when client_secret.json is missing."""
    # Patch the path to a non-existent file
    # No need to import config here, monkeypatch targets the module directly
    monkeypatch.setattr(config, 'SECRETS_PATH', 'non_existent_file.json')
    # Now call the function from the config module
    oauth_config = config.load_oauth_config()
    assert oauth_config == {} # Should return empty dict on error

def test_load_oauth_config_invalid_json(tmp_path, monkeypatch):
    """Verify behavior with invalid JSON."""
    secrets_file = tmp_path / "invalid_secret.json"
    secrets_file.write_text("this is not json", encoding='utf-8')
    monkeypatch.setattr(config, 'SECRETS_PATH', str(secrets_file))
    # Call the function from the config module
    oauth_config = config.load_oauth_config()
    assert oauth_config == {}

def test_folder_initialization(tmp_path):
    """Test that initialize_folders creates directories."""
    # Temporarily point config folders to new subdirs in tmp_path
    tokens = tmp_path / "t"
    data = tmp_path / "d"
    temp = data / "temp"
    static = tmp_path / "s"

    # Use monkeypatch from pytest fixture is easier, but showing manual patch:
    # Need to import patch for this approach
    from unittest.mock import patch
    with patch('config.TOKENS_FOLDER', str(tokens)), \
         patch('config.DATA_FOLDER', str(data)), \
         patch('config.TEMP_FOLDER', str(temp)), \
         patch('config.STATIC_FOLDER', str(static)):

        from config import initialize_folders
        initialize_folders()

        assert tokens.is_dir()
        assert data.is_dir()
        assert temp.is_dir()
        assert static.is_dir()
        assert (static / "favicon.ico").is_file() # Checks dummy favicon creation
