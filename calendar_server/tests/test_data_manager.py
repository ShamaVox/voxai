import os
import json
import pytest
# Removed Path import, using strings directly
import data_manager
# Get paths as strings from fixture patching config
from config import TOKENS_FOLDER, DATA_FOLDER

# Fixture `temp_folders` from conftest.py automatically handles setting up
# TOKENS_FOLDER and DATA_FOLDER in a temporary directory. It patches them as strings.

def test_get_token_files_empty(temp_folders):
    assert data_manager.get_token_files() == []

def test_load_token_data_invalid_json(temp_folders):
    user_id = "invalid_json_user"
    # Use os.path.join to create the file path
    file_path = os.path.join(TOKENS_FOLDER, f"{user_id}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("{ invalid json")

    loaded_data = data_manager.load_token_data(f"{user_id}.json")
    assert loaded_data == {} # Expect empty dict if JSON is invalid

def test_load_user_data_not_found(temp_folders):
    # Load data for a user whose file doesn't exist
    loaded_data = data_manager.load_user_data("new_user")

    # Should return the default structure
    expected_default = {
        "meetings": [],
        "recall_calendar_id": None,
        "bots": {},
        "last_updated": None
    }
    assert loaded_data == expected_default

def test_load_user_data_invalid_json(temp_folders):
    user_id = "corrupt_user"
    # Use os.path.join for the path
    file_path = os.path.join(DATA_FOLDER, f"{user_id}_data.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("}invalid json{")

    loaded_data = data_manager.load_user_data(user_id)
    # Should return the default structure if file is corrupt
    expected_default = {
        "meetings": [],
        "recall_calendar_id": None,
        "bots": {},
        "last_updated": None
    }
    assert loaded_data == expected_default
