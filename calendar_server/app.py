import json
import os
import time
import sys
import uuid
import subprocess
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from flask import Flask, jsonify, request, redirect, send_from_directory

# Import RecallAPI from the hex folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hex.recall import RecallAPI, download_video

# Create Flask app
app = Flask(__name__)

# Configuration
CHECK_INTERVAL = 3600  # How often to check for calendar updates (in seconds)
TOKENS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tokens")
DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TEMP_FOLDER = os.path.join(DATA_FOLDER, "temp")

def load_oauth_config():
    """Load OAuth configuration from client_secret.json file."""
    secrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secret.json")
    try:
        with open(secrets_path, 'r') as f:
            secrets = json.load(f)
            web_config = secrets.get('web', {})
            return {
                'client_id': web_config.get('client_id'),
                'client_secret': web_config.get('client_secret'),
                'redirect_uri': web_config.get('redirect_uris', [''])[0],  # Use first redirect URI
                'auth_uri': web_config.get('auth_uri'),
                'token_uri': web_config.get('token_uri')
            }
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error loading OAuth config: {str(e)}")
        return {}

# Ensure folders exist
os.makedirs(TOKENS_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Token management functions
def get_token_files():
    """Get a list of all token files in the tokens folder."""
    return [f for f in os.listdir(TOKENS_FOLDER) if f.endswith('.json') and not f.endswith('_meetings.json')]

def load_token_data(token_file):
    """Load token data from a token file."""
    with open(os.path.join(TOKENS_FOLDER, token_file), 'r') as f:
        return json.load(f)

def refresh_token_if_needed(token_data, token_file):
    """Refresh token if expired and update token file."""
    # Check if all required fields for token refresh are present
    required_fields = ['refresh_token', 'token_uri', 'client_id', 'client_secret']
    missing_fields = [field for field in required_fields if field not in token_data or not token_data[field]]
    
    if missing_fields:
        print(f"Warning: Token file {token_file} is missing required fields for refresh: {', '.join(missing_fields)}")
        print("This token cannot be refreshed automatically. Please re-authenticate.")
        return None
    
    try:
        creds = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes')
        )
        
        if not creds.valid:
            print(f"Refreshing token for {token_file}...")
            creds.refresh(Request())
            
            # Update token data
            token_data['token'] = creds.token
            if creds.refresh_token:
                token_data['refresh_token'] = creds.refresh_token
            if creds.expiry:
                token_data['expiry'] = creds.expiry.isoformat().replace('+00:00', 'Z')
            
            # Save updated token data
            with open(os.path.join(TOKENS_FOLDER, token_file), 'w') as f:
                json.dump(token_data, f, indent=2)
            
            print(f"Token refreshed for {token_file}")
        
        return creds
    except Exception as e:
        print(f"Error refreshing token for {token_file}: {str(e)}")
        return None

# User data management
def load_user_data(user_id):
    """Load saved data for a user."""
    data_file = os.path.join(DATA_FOLDER, f"{user_id}_data.json")
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            return json.load(f)
    return {
        "meetings": [],
        "recall_calendar_id": None,
        "bots": {},  # Map of meeting ID to bot data
        "last_updated": None
    }

def save_user_data(user_id, data):
    """Save data for a user."""
    data_file = os.path.join(DATA_FOLDER, f"{user_id}_data.json")
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)

def extract_meeting_url(event):
    """Extract meeting URL from a Recall calendar event."""
    # Recall API already provides meeting URLs
    meeting_url = event.get('meeting_url', '')
    
    # If no meeting URL found, check the event details
    if not meeting_url and 'raw' in event:
        raw_event = event['raw']
        # Check different conference data formats based on platform
        if 'conferenceData' in raw_event:
            conf_data = raw_event['conferenceData']
            if 'entryPoints' in conf_data:
                for entry in conf_data['entryPoints']:
                    if entry.get('uri'):
                        meeting_url = entry.get('uri')
                        break
        
        # Try location as a fallback (might contain Zoom/Teams links)
        if not meeting_url and 'location' in raw_event:
            location = raw_event['location']
            if location:
                # Simple pattern matching for Zoom/Teams links
                for word in location.split():
                    if any(domain in word.lower() for domain in ['zoom.us', 'teams.microsoft.com', 'meet.google.com']):
                        meeting_url = word
                        break
    
    return meeting_url

def find_meeting_changes(old_meetings, new_meetings):
    """
    Compare old and new meetings to find:
    - New meetings
    - Changed meetings (time/date changes)
    - Removed meetings
    """
    old_meetings_dict = {m['id']: m for m in old_meetings}
    new_meetings_dict = {m['id']: m for m in new_meetings}
    
    new_meeting_ids = set(new_meetings_dict.keys()) - set(old_meetings_dict.keys())
    removed_meeting_ids = set(old_meetings_dict.keys()) - set(new_meetings_dict.keys())
    
    changed_meeting_ids = set()
    for meeting_id in set(old_meetings_dict.keys()) & set(new_meetings_dict.keys()):
        old_meeting = old_meetings_dict[meeting_id]
        new_meeting = new_meetings_dict[meeting_id]
        
        # Check if start or end time has changed
        old_start = old_meeting.get('start_time', '')
        new_start = new_meeting.get('start_time', '')
        old_end = old_meeting.get('end_time', '')
        new_end = new_meeting.get('end_time', '')
        
        if old_start != new_start or old_end != new_end:
            changed_meeting_ids.add(meeting_id)
    
    # Get the actual meeting objects
    new_meetings_list = [new_meetings_dict[id] for id in new_meeting_ids]
    changed_meetings_list = [new_meetings_dict[id] for id in changed_meeting_ids]
    
    return {
        'new': new_meetings_list,
        'changed': changed_meetings_list,
        'removed': list(removed_meeting_ids)
    }

# Audio processing functions
def convert_to_mp3(video_path, bitrate='192k'):
    """Convert MP4 to MP3 using ffmpeg."""
    try:
        mp3_path = video_path.replace('.mp4', '.mp3')
        
        # Use ffmpeg for conversion
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # No video
            '-ar', '44100',  # Audio sample rate
            '-ac', '2',  # Audio channels
            '-b:a', bitrate,  # Audio bitrate
            '-f', 'mp3',  # Format
            mp3_path
        ]
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Error converting video to MP3: {stderr.decode()}")
            return None
            
        return mp3_path
        
    except Exception as e:
        print(f"Error converting video to MP3: {str(e)}")
        return None

def upload_to_s3(file_path, s3_key):
    """Upload file to S3 bucket."""
    try:
        # Configure S3 client from environment variables
        s3_bucket = os.environ.get('S3_BUCKET')
        if not s3_bucket:
            print("S3_BUCKET environment variable not set")
            return None
            
        s3_client = boto3.client('s3')
        
        # Upload file
        s3_client.upload_file(
            file_path, 
            s3_bucket, 
            s3_key,
            ExtraArgs={'ContentType': 'audio/mpeg'}
        )
        
        # Generate URL
        s3_url = f"s3://{s3_bucket}/{s3_key}"
        return s3_url
        
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        return None

# Recall API functions
def list_calendar_events(recall_api, calendar_id):
    """List calendar events from Recall API."""
    # Calculate time range for the next 7 days
    now = datetime.utcnow()
    start_time = now.isoformat() + 'Z'
    end_time = (now + timedelta(days=7)).isoformat() + 'Z'
    
    events = []
    next_url = f"https://us-west-2.recall.ai/api/v2/calendar-events/?calendar_id={calendar_id}&start_time__gte={start_time}&start_time__lte={end_time}"
    
    while next_url:
        response = requests.get(next_url, headers=recall_api.get_headers())
        result, status = recall_api.handle_response(response)
        
        if status != 200:
            print(f"Error fetching calendar events: {status}")
            print(json.dumps(result, indent=2))
            break
        
        # Add events from this page
        events.extend(result.get('results', []))
        
        # Check if there's another page
        next_url = result.get('next')
    
    return events

def process_recall_events(events):
    """Process Recall calendar events into a standard format."""
    meetings = []
    
    for event in events:
        # Skip deleted events
        if event.get('is_deleted', False):
            continue
        
        meeting_url = extract_meeting_url(event)
        
        meeting_info = {
            'id': event.get('id'),
            'title': event.get('title', 'No Title'),
            'start_time': event.get('start_time'),
            'end_time': event.get('end_time'),
            'meeting_url': meeting_url,
            'calendar_id': event.get('calendar_id'),
            'ical_uid': event.get('ical_uid'),
            'bot': event.get('bot'),
            'raw_data': event.get('raw', {})
        }
        meetings.append(meeting_info)
    
    return meetings

def create_calendar_integration(recall_api, token_data):
    """Create a calendar integration in Recall API."""
    response, status_code = recall_api.create_calendar(
        oauth_client_id=token_data.get('client_id'),
        oauth_client_secret=token_data.get('client_secret'),
        oauth_refresh_token=token_data.get('refresh_token'),
        platform="google_calendar"
    )
    
    if status_code == 201:
        print("Calendar created successfully in Recall API!")
        return response.get('id')
    else:
        print(f"Failed to create calendar in Recall API. Status code: {status_code}")
        print(json.dumps(response, indent=2))
        return None

def schedule_recall_bot(recall_api, calendar_event_id, meeting_url):
    """Schedule a Recall bot for a calendar event."""
    if not meeting_url:
        print(f"No meeting URL found for event {calendar_event_id}, skipping bot scheduling")
        return None
    
    # Generate a deduplication key
    deduplication_key = f"event_{calendar_event_id}_{uuid.uuid4()}"
    
    # Bot configuration
    bot_config = {
        "meeting_url": meeting_url,
        "bot_name": "VoxAI Bot",
        "recording_mode": "speaker_view",
        "automatic_leave": {
            "everyone_left_timeout": 150
        }
    }
    
    data = {
        "deduplication_key": deduplication_key,
        "bot_config": bot_config
    }
    
    url = f"https://us-west-2.recall.ai/api/v2/calendar-events/{calendar_event_id}/bot/"
    
    response = requests.post(
        url,
        headers=recall_api.get_headers(),
        json=data
    )
    
    result, status = recall_api.handle_response(response)
    
    if 200 <= status < 300:
        print(f"Bot scheduled successfully for event {calendar_event_id}")
        return result
    else:
        print(f"Failed to schedule bot for event {calendar_event_id}. Status: {status}")
        print(json.dumps(result, indent=2))
        return None

def unschedule_recall_bot(recall_api, calendar_event_id):
    """Unschedule a Recall bot from a calendar event."""
    url = f"https://us-west-2.recall.ai/api/v2/calendar-events/{calendar_event_id}/bot/"
    
    response = requests.delete(
        url,
        headers=recall_api.get_headers()
    )
    
    result, status = recall_api.handle_response(response)
    
    if 200 <= status < 300:
        print(f"Bot unscheduled successfully for event {calendar_event_id}")
        return True
    else:
        print(f"Failed to unschedule bot for event {calendar_event_id}. Status: {status}")
        print(json.dumps(result, indent=2))
        return False

def check_finished_meetings():
    """Check all users for finished meetings that need to be processed."""
    print(f"\n{datetime.now().isoformat()} - Checking for finished meetings...")
    
    # Initialize Recall API
    recall_api = RecallAPI()
    
    # Get all user data files
    user_data_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('_data.json')]
    processed_meetings = 0
    removed_bots = 0
    
    for data_file in user_data_files:
        user_id = data_file.replace('_data.json', '')
        print(f"Checking finished meetings for user: {user_id}")
        
        # Load user data
        user_data = load_user_data(user_id)
        user_data_modified = False
        
        # Get all bot IDs that haven't been processed yet
        unprocessed_bots = {}
        bots_to_remove = set()
        
        for meeting_id, bot_data in user_data.get('bots', {}).items():
            if not bot_data.get('audio_processed', False) and 'bot_id' in bot_data:
                unprocessed_bots[bot_data['bot_id']] = meeting_id
                
                # If this meeting was marked as removed over 24 hours ago and still not processed,
                # we might need to eventually give up on it
                if bot_data.get('meeting_removed', False) and 'removed_at' in bot_data:
                    try:
                        removed_time = datetime.fromisoformat(bot_data['removed_at'])
                        # If it's been more than 24 hours, check if the bot still exists
                        if (datetime.now() - removed_time).total_seconds() > 86400:  # 24 hours
                            # We'll verify if these bots still exist
                            bots_to_remove.add(bot_data['bot_id'])
                    except (ValueError, TypeError):
                        pass
        
        if not unprocessed_bots:
            print(f"No unprocessed bots found for user {user_id}")
            continue
            
        print(f"Found {len(unprocessed_bots)} unprocessed bots for user {user_id}")
        
        # Check which bots have finished
        finished_bots = recall_api.list_finished_bots(list(unprocessed_bots.keys()))
        
        print(f"Found {len(finished_bots)} finished bots for user {user_id}")
        
        # For bots that might need removal, check if they still exist
        if bots_to_remove:
            bots_to_actually_remove = set()
            for bot_id in bots_to_remove:
                bot_details, status_code = recall_api.check_bot_status(bot_id)
                # If bot doesn't exist (404) or some other error, mark for removal
                if status_code == 404 or (status_code != 200 and not bot_details.get('video_url')):
                    bots_to_actually_remove.add(bot_id)
            
            # Remove bots that don't exist anymore
            for bot_id in bots_to_actually_remove:
                meeting_id = unprocessed_bots[bot_id]
                print(f"Bot {bot_id} for meeting {meeting_id} no longer exists, removing")
                del user_data['bots'][meeting_id]
                removed_bots += 1
                user_data_modified = True
        
        # Process each finished bot
        for bot_id, bot_details in finished_bots.items():
            meeting_id = unprocessed_bots[bot_id]
            print(f"Processing finished meeting {meeting_id} (bot {bot_id})")
            
            # Create temp directory if it doesn't exist
            os.makedirs(TEMP_FOLDER, exist_ok=True)
            
            # Check if we already have the MP3 in S3
            s3_key = f"{user_id}/{meeting_id}/recording.mp3"
            if file_exists_in_s3(s3_key):
                print(f"MP3 already exists in S3 for meeting {meeting_id}, skipping download")
                s3_url = f"s3://{os.environ.get('S3_BUCKET')}/{s3_key}"
                
                # Update user data
                user_data['bots'][meeting_id].update({
                    'audio_processed': True,
                    'audio_url': s3_url,
                    'processed_at': datetime.now().isoformat()
                })
                
                processed_meetings += 1
                user_data_modified = True
                continue
            
            # Check if we already have the MP4 locally
            mp4_path = os.path.join(TEMP_FOLDER, f"{bot_id}.mp4")
            mp3_path = os.path.join(TEMP_FOLDER, f"{bot_id}.mp3")
            metadata_path = os.path.join(TEMP_FOLDER, f"{bot_id}.json")
            
            participants = []
            
            # If MP4 exists but not MP3, just do conversion
            if os.path.exists(mp4_path) and not os.path.exists(mp3_path):
                print(f"MP4 exists but MP3 doesn't for meeting {meeting_id}, doing conversion")
                
                # Extract participants info from bot details
                participants = bot_details.get('meeting_participants_names', [])
                
                # Convert MP4 to MP3
                command = [
                    'ffmpeg',
                    '-i', mp4_path,
                    '-vn',  # No video
                    '-ar', '44100',  # Audio sample rate
                    '-ac', '2',  # Audio channels
                    '-b:a', '192k',  # Audio bitrate
                    '-f', 'mp3',  # Format
                    mp3_path
                ]
                
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    print(f"Error converting video to MP3: {stderr.decode()}")
                    continue
            # Otherwise, download video and convert
            elif not os.path.exists(mp3_path):
                print(f"Downloading video for meeting {meeting_id}")
                
                # Download the video
                video_path, participants = download_video(bot_id, os.path.join(TEMP_FOLDER, bot_id))
                if not video_path:
                    print(f"Failed to download video for bot {bot_id}")
                    continue
                
                # Convert to MP3
                command = [
                    'ffmpeg',
                    '-i', video_path,
                    '-vn',  # No video
                    '-ar', '44100',  # Audio sample rate
                    '-ac', '2',  # Audio channels
                    '-b:a', '192k',  # Audio bitrate
                    '-f', 'mp3',  # Format
                    mp3_path
                ]
                
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    print(f"Error converting video to MP3: {stderr.decode()}")
                    continue
            
            # Prepare metadata
            metadata = {
                'meeting_id': meeting_id,
                'bot_id': bot_id,
                'user_id': user_id,
                'title': bot_details.get('meeting_title', ''),
                'participants': participants,
                'start_time': bot_details.get('start_time'),
                'end_time': bot_details.get('end_time'),
                'processing_time': datetime.now().isoformat()
            }
            
            # Save metadata to JSON file
            save_meeting_metadata(metadata, metadata_path)
            
            # Upload MP3 to S3
            s3_audio_key = f"{user_id}/{meeting_id}/recording.mp3"
            s3_audio_url = upload_to_s3(mp3_path, s3_audio_key)
            
            # Upload metadata to S3
            s3_meta_key = f"{user_id}/{meeting_id}/metadata.json"
            s3_meta_url = upload_to_s3(metadata_path, s3_meta_key)
            
            if s3_audio_url and s3_meta_url:
                # Update user data
                user_data['bots'][meeting_id].update({
                    'audio_processed': True,
                    'audio_url': s3_audio_url,
                    'metadata_url': s3_meta_url,
                    'participants': participants,
                    'processed_at': datetime.now().isoformat()
                })
                
                # Clean up local files
                if os.path.exists(mp4_path):
                    os.remove(mp4_path)
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                
                processed_meetings += 1
                user_data_modified = True
                print(f"Successfully processed meeting {meeting_id}")
            else:
                print(f"Failed to upload files to S3 for meeting {meeting_id}")
        
        # Save updated user data if modified
        if user_data_modified:
            save_user_data(user_id, user_data)
    
    print(f"Finished checking meetings. Processed {processed_meetings} recordings. Removed {removed_bots} bots.")
    return processed_meetings

# Add a new API endpoint for manually checking finished meetings
@app.route('/check-finished')
def check_finished_endpoint():
    """Endpoint to check for finished meetings."""
    try:
        processed = check_finished_meetings()
        return jsonify({
            'status': 'ok',
            'processed_meetings': processed,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Main processing function
def process_user_calendar(user_id, token_data):
    """Process a user's calendar for changes and schedule/unschedule bots as needed."""
    try:
        # Initialize Recall API
        recall_api = RecallAPI()
        
        # Load user data
        user_data = load_user_data(user_id)
        
        # Refresh token if needed
        creds = refresh_token_if_needed(token_data, f"{user_id}.json")
        if creds is None:
            print(f"Cannot process calendar for user {user_id} due to invalid credentials")
            return False
        
        # Get or create calendar in Recall
        calendar_id = user_data.get('recall_calendar_id')
        if not calendar_id:
            calendar_id = create_calendar_integration(recall_api, token_data)
            if calendar_id:
                user_data['recall_calendar_id'] = calendar_id
                save_user_data(user_id, user_data)
            else:
                print(f"Could not create calendar for user {user_id}")
                return False
        
        # Get upcoming meetings from Recall API
        events = list_calendar_events(recall_api, calendar_id)
        meetings = process_recall_events(events)
        
        # Find changes compared to previous meetings
        old_meetings = user_data.get('meetings', [])
        changes = find_meeting_changes(old_meetings, meetings)
        
        # Process new meetings
        for meeting in changes['new']:
            meeting_id = meeting['id']
            meeting_url = meeting.get('meeting_url')
            
            if meeting_url:
                bot_result = schedule_recall_bot(recall_api, meeting_id, meeting_url)
                if bot_result:
                    user_data.setdefault('bots', {})[meeting_id] = {
                        'bot_id': bot_result.get('bots')[0]['bot_id'],
                        'meeting_url': meeting_url,
                        'scheduled_at': datetime.now().isoformat()
                    }
        
        # Process changed meetings
        for meeting in changes['changed']:
            meeting_id = meeting['id']
            meeting_url = meeting.get('meeting_url')
            
            # First unschedule existing bot
            if meeting_id in user_data.get('bots', {}):
                print(f"Unscheduling bot for changed meeting {meeting_id}")
                unschedule_result = unschedule_recall_bot(recall_api, meeting_id)
                
                # Even if unscheduling fails, we can try to schedule a new bot
                if not unschedule_result:
                    print(f"Warning: Failed to unschedule bot for meeting {meeting_id}, will still try to schedule new bot")
            
            # Then schedule new bot if meeting URL exists
            if meeting_url:
                print(f"Scheduling new bot for changed meeting {meeting_id}")
                bot_result = schedule_recall_bot(recall_api, meeting_id, meeting_url)
                
                if bot_result and 'bots' in bot_result and bot_result['bots']:
                    print(f"Successfully scheduled new bot for meeting {meeting_id}")
                    user_data.setdefault('bots', {})[meeting_id] = {
                        'bot_id': bot_result['bots'][0]['bot_id'],
                        'meeting_url': meeting_url,
                        'scheduled_at': datetime.now().isoformat()
                    }
                else:
                    print(f"Failed to schedule new bot for meeting {meeting_id}")
                    # If we failed to schedule a new bot after unscheduling the old one,
                    # we should remove this meeting from the bots dictionary
                    if meeting_id in user_data.get('bots', {}):
                        del user_data['bots'][meeting_id]
        
        # Process removed meetings
        for meeting_id in changes['removed']:
            if meeting_id in user_data.get('bots', {}):
                bot_data = user_data['bots'][meeting_id]
                
                # If the meeting was in the past and has a bot, don't unschedule, just mark for recording check
                # Parse the end time of the meeting from our stored data to check if it's in the past
                meeting_end_time = None
                for meeting in old_meetings:
                    if meeting['id'] == meeting_id and 'end_time' in meeting:
                        try:
                            meeting_end_time = datetime.fromisoformat(meeting['end_time'].replace('Z', '+00:00'))
                        except (ValueError, TypeError):
                            meeting_end_time = None
                        break
                        
                # Check if the meeting has ended
                if meeting_end_time and meeting_end_time < datetime.now(timezone.utc):
                    print(f"Meeting {meeting_id} has ended, marking for recording check")
                    # Don't unschedule - keep the bot to get the recording
                    bot_data['meeting_removed'] = True
                    bot_data['removed_at'] = datetime.now().isoformat()
                else:
                    # Meeting is in the future or we can't determine - unschedule normally
                    print(f"Meeting {meeting_id} removed from calendar, unscheduling bot")
                    unschedule_recall_bot(recall_api, meeting_id)
                    del user_data['bots'][meeting_id]
        
        # Update and save user data
        user_data['meetings'] = meetings
        user_data['last_updated'] = datetime.now().isoformat()
        save_user_data(user_id, user_data)
        
        print(f"Processed calendar for user {user_id}: {len(changes['new'])} new, "
              f"{len(changes['changed'])} changed, {len(changes['removed'])} removed")
        
        return True
    
    except Exception as e:
        print(f"Error processing calendar for user {user_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_all_calendars():
    """Check all user calendars for updates and process finished meetings."""
    print(f"\n{datetime.now().isoformat()} - Checking for calendar updates...")
    
    # Get all token files
    token_files = get_token_files()
    print(f"Found {len(token_files)} token files")
    
    for token_file in token_files:
        user_id = os.path.splitext(token_file)[0]
        print(f"\nProcessing user: {user_id}")
        
        try:
            token_data = load_token_data(token_file)
            process_user_calendar(user_id, token_data)
        except Exception as e:
            print(f"Error processing user {user_id}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Check for finished meetings and process them
    check_finished_meetings()
    
    print(f"\nFinished checking calendars.")
    return True

@app.route('/auth/google')
def google_auth():
    """Redirect user to Google OAuth page."""
    # Get OAuth config from client_secret.json
    oauth_config = load_oauth_config()
    
    # Hard-code the redirect URI to match exactly what's in Google Console
    redirect_uri = "http://localhost:8080/auth/google/callback"  # Update to match Google Console
    
    if not oauth_config.get('client_id'):
        return "OAuth configuration missing. Please ensure client_secret.json is properly configured.", 500
    
    # Define OAuth scopes for calendar access
    scopes = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/calendar.events.readonly',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'openid'
    ]
    
    # Build the authorization URL
    auth_url = (
        oauth_config.get('auth_uri', "https://accounts.google.com/o/oauth2/auth") +
        f"?client_id={oauth_config['client_id']}" +
        f"&redirect_uri={redirect_uri}" +
        "&response_type=code" +
        f"&scope={'+'.join(scopes)}" +
        "&access_type=offline" +
        "&prompt=consent"  # Force refresh token generation
    )
    
    return redirect(auth_url)

@app.route('/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback."""
    auth_code = request.args.get('code')
    if not auth_code:
        return "Authorization failed: No code received", 400
    
    # Get OAuth config
    oauth_config = load_oauth_config()
    
    if not oauth_config.get('client_id') or not oauth_config.get('client_secret'):
        return "OAuth configuration missing", 500
    
    # Use the exact same redirect URI as in the auth request
    redirect_uri = "http://localhost:8080/auth/google/callback"  # Must match Google Console configuration
    
    # Exchange code for credentials
    try:
        # Create flow using client_secret.json
        from google_auth_oauthlib.flow import Flow
        
        # Create flow instance directly with our parameters
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": oauth_config['client_id'],
                    "client_secret": oauth_config['client_secret'],
                    "auth_uri": oauth_config.get('auth_uri', "https://accounts.google.com/o/oauth2/auth"),
                    "token_uri": oauth_config.get('token_uri', "https://oauth2.googleapis.com/token"),
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=[
                'https://www.googleapis.com/auth/calendar.readonly',
                'https://www.googleapis.com/auth/calendar.events.readonly',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'openid'
            ]
        )
        
        flow.redirect_uri = redirect_uri
        
        # Use the authorization code and get credentials
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        
        # Get user info using credentials
        def get_user_info(credentials):
            """Get user info to identify the account using direct HTTP request."""
            try:
                # Print debug info
                print(f"Token present: {bool(credentials.token)}")
                print(f"Token expires: {credentials.expiry}")
                
                # Make a direct HTTP request with the token
                headers = {'Authorization': f'Bearer {credentials.token}'}
                response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error getting user info. Status: {response.status_code}, Response: {response.text}")
                    return None
            except Exception as e:
                print(f"Exception in get_user_info: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
        
        user_info = get_user_info(credentials)
        
        if not user_info or 'id' not in user_info:
            print(f"Failed to get valid user info: {user_info}")
            return "Could not identify user", 400
            
        user_id = user_info.get('email', user_info.get('id'))
        print(f"User identified as: {user_id}")
        
        # Save token data
        token_file_path = os.path.join(TOKENS_FOLDER, f"{user_id}.json")
        
        # Prepare token data in the format expected by our app
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        # Save token data
        with open(token_file_path, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        # Process calendar immediately
        try:
            process_user_calendar(user_id, token_data)
        except Exception as e:
            print(f"Error during initial calendar processing: {str(e)}")
        
        return "Authentication successful! Your calendar is now being processed. You can close this window."
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error during authentication: {str(e)}", 500

# Flask routes
@app.route('/')
def index():
    """Main page with instructions."""
    return """
    <html>
    <head><title>Calendar Recording Service</title></head>
    <body>
        <h1>Calendar Recording Service</h1>
        <p>This server automatically records your meetings from Google Calendar.</p>
        <p><a href="/auth/google">Click here to connect your Google Calendar</a></p>
    </body>
    </html>
    """

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/stats')
def stats():
    """Get basic stats about users and meetings."""
    try:
        token_files = get_token_files()
        users = []
        
        for token_file in token_files:
            user_id = os.path.splitext(token_file)[0]
            user_data = load_user_data(user_id)
            
            users.append({
                'user_id': user_id,
                'calendar_id': user_data.get('recall_calendar_id'),
                'meetings_count': len(user_data.get('meetings', [])),
                'bots_count': len(user_data.get('bots', {})),
                'last_updated': user_data.get('last_updated')
            })
        
        return jsonify({
            'users_count': len(users),
            'users': users,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/check-now')
def trigger_check():
    """Manually trigger calendar checking."""
    try:
        check_all_calendars()
        return jsonify({
            'status': 'ok',
            'message': 'Calendar check completed',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Print and handle all exceptions."""
    request_info = {
        "url": request.path,
        "method": request.method,
        "args": dict(request.args),
        "form": dict(request.form) if request.form else None,
        "json": request.get_json(silent=True),
        "headers": {k: v for k, v in request.headers.items() if k.lower() not in ('cookie', 'authorization')}
    }
    
    print(f"Exception in request to {request.method} {request.path}: {str(e)}")
    print(f"Request details: {request_info}")
    import traceback
    traceback.print_exc()
    return f"Server error: {str(e)}", 500

# Flask CLI commands
@app.cli.command('check-calendars')
def check_calendars_command():
    """CLI command to check calendars once."""
    check_all_calendars()

@app.cli.command('run-scheduler')
def run_scheduler():
    """CLI command to run the scheduler continuously."""
    try:
        print("Starting Calendar Server...")
        while True:
            check_all_calendars()
            print(f"Next check in {CHECK_INTERVAL} seconds")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server stopped due to error: {str(e)}")
        import traceback
        traceback.print_exc()

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

def file_exists_in_s3(s3_key):
    """Check if a file exists in S3 bucket."""
    try:
        s3_bucket = os.environ.get('S3_BUCKET')
        if not s3_bucket:
            return False
            
        s3_client = boto3.client('s3')
        response = s3_client.list_objects_v2(
            Bucket=s3_bucket,
            Prefix=s3_key,
            MaxKeys=1
        )
        
        return 'Contents' in response and len(response['Contents']) > 0
    except Exception as e:
        print(f"Error checking S3 for file {s3_key}: {str(e)}")
        return False

# Add function to save meeting metadata as JSON
def save_meeting_metadata(meeting_data, output_path):
    """Save meeting metadata to a JSON file."""
    try:
        with open(output_path, 'w') as f:
            json.dump(meeting_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving meeting metadata: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting Calendar Server in standalone mode...")
    try:
        while True:
            check_all_calendars()
            print(f"Next check in {CHECK_INTERVAL} seconds")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
