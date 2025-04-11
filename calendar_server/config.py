import os
import json
from datetime import timedelta

# --- Core Configuration ---
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
TOKENS_FOLDER = os.path.join(APP_ROOT, "tokens")
DATA_FOLDER = os.path.join(APP_ROOT, "data")
TEMP_FOLDER = os.path.join(DATA_FOLDER, "temp")
STATIC_FOLDER = os.path.join(APP_ROOT, "static") # For favicon etc.

# --- Scheduling ---
CHECK_INTERVAL = 3600  # How often to check for calendar updates (in seconds)
MEETING_LOOKAHEAD_DAYS = 7 # How many days ahead to check for meetings
BOT_REMOVAL_CHECK_HOURS = 24 # How long after a meeting is removed to keep checking for the bot

# --- OAuth Configuration ---
SECRETS_PATH = os.path.join(APP_ROOT, "client_secret.json")

def load_oauth_config():
    """Load OAuth configuration from client_secret.json file."""
    try:
        with open(SECRETS_PATH, 'r') as f:
            secrets = json.load(f)
            web_config = secrets.get('web', {})
            # Ensure the redirect URI used matches exactly what's registered in Google Console
            # This might need adjustment based on deployment (http vs https, domain)
            redirect_uri = web_config.get('redirect_uris', ['http://localhost:8080/auth/google/callback'])[0]
            return {
                'client_id': web_config.get('client_id'),
                'client_secret': web_config.get('client_secret'),
                'redirect_uri': redirect_uri,
                'auth_uri': web_config.get('auth_uri'),
                'token_uri': web_config.get('token_uri')
            }
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error loading OAuth config from {SECRETS_PATH}: {str(e)}")
        return {}

OAUTH_CONFIG = load_oauth_config()
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

# --- Recall API Configuration ---
# Assumes RECALL_API_KEY is set as an environment variable for RecallAPI()
RECALL_API_BASE_URL = "https://us-west-2.recall.ai/api/v2"
RECALL_BOT_NAME = "VoxAI Bot"

# --- Media Processing ---
FFMPEG_BITRATE = '192k'
FFMPEG_SAMPLE_RATE = '44100'
FFMPEG_CHANNELS = 2

# --- S3 Configuration ---
# TODO: test
S3_BUCKET = os.environ.get('S3_BUCKET')

# --- Folder Initialization ---
def initialize_folders():
    """Ensure necessary folders exist."""
    os.makedirs(TOKENS_FOLDER, exist_ok=True)
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    os.makedirs(STATIC_FOLDER, exist_ok=True) # Ensure static folder exists

    # Add a basic favicon if it doesn't exist to avoid 404s
    favicon_path = os.path.join(STATIC_FOLDER, 'favicon.ico')
    if not os.path.exists(favicon_path):
        with open(favicon_path, 'w') as f:
            f.write('') # Simplest placeholder
        print(f"Created placeholder favicon at {favicon_path}")
