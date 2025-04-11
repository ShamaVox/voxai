import os
import json
from config import TOKENS_FOLDER, DATA_FOLDER

def get_token_files() -> list[str]:
    """Get a list of all user token files (excluding meeting tokens)."""
    if not os.path.exists(TOKENS_FOLDER):
        return []
    return [f for f in os.listdir(TOKENS_FOLDER) if f.endswith('.json') and not f.endswith('_meetings.json')]

def load_token_data(token_file: str) -> dict:
    """Load token data from a specific token file."""
    file_path = os.path.join(TOKENS_FOLDER, token_file)
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading token file {token_file}: {e}")
        return {} # Return empty dict on error

def save_token_data(user_id: str, token_data: dict):
    """Save token data for a user."""
    token_file_path = os.path.join(TOKENS_FOLDER, f"{user_id}.json")
    try:
        with open(token_file_path, 'w') as f:
            json.dump(token_data, f, indent=2)
    except IOError as e:
        print(f"Error saving token file for {user_id}: {e}")


def load_user_data(user_id: str) -> dict:
    """Load saved application data for a user."""
    data_file = os.path.join(DATA_FOLDER, f"{user_id}_data.json")
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
             print(f"Error decoding JSON for user {user_id}: {e}. Returning default structure.")
    # Return default structure if file doesn't exist or is corrupt
    return {
        "meetings": [],             # List of meetings from last sync
        "recall_calendar_id": None, # Recall's ID for this user's calendar
        "bots": {},                 # { meeting_id: { bot_id: ..., status: ... } }
        "last_updated": None        # ISO timestamp of last successful sync
    }

def save_user_data(user_id: str, data: dict):
    """Save application data for a user."""
    data_file = os.path.join(DATA_FOLDER, f"{user_id}_data.json")
    try:
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error saving data file for {user_id}: {e}")
