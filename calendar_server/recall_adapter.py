import os
import sys
import json
import uuid
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Tuple, Optional
import time # Import time for potential delays/retries if needed
import shutil # Import shutil for renaming

# Import RecallAPI from the hex folder (adjust path as needed)
# Hex folder is one level above the directory containing this script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hex.recall import RecallAPI, download_video as recall_download_video

# Import config values
import config # Import config module directly
from config import (RECALL_API_BASE_URL, MEETING_LOOKAHEAD_DAYS, RECALL_BOT_NAME,
                    TEMP_FOLDER, S3_BUCKET, BOT_REMOVAL_CHECK_HOURS) # Use imported config
from utils import extract_meeting_url, save_meeting_metadata
from media_processing import convert_to_mp3, upload_to_s3, file_exists_in_s3, cleanup_temp_files

# Initialize Recall API client globally or pass it around
# Later on, dependency injection might be better.
recall_api = RecallAPI()

def list_calendar_events(calendar_id: str) -> list[dict]:
    """List upcoming calendar events from Recall API for a specific calendar."""
    now = datetime.now(timezone.utc)
    start_time_str = now.isoformat().replace('+00:00', 'Z')
    end_time = now + timedelta(days=MEETING_LOOKAHEAD_DAYS)
    end_time_str = end_time.isoformat().replace('+00:00', 'Z')

    events = []
    # Note: Recall API v2 endpoint structure might differ slightly. Adjust if needed.
    # Example uses v2 structure based on original code context.
    next_url = (f"{RECALL_API_BASE_URL}/calendar-events/"
                f"?calendar_id={calendar_id}"
                f"&start_time__gte={start_time_str}"
                f"&start_time__lte={end_time_str}"
                f"&limit=100") # Use pagination limit

    print(f"Fetching Recall events for calendar {calendar_id} from {start_time_str} to {end_time_str}")

    while next_url:
        try:
            response = requests.get(next_url, headers=recall_api.get_headers())
            # Use RecallAPI's handler, ensure it exists or provide default
            if hasattr(recall_api, 'handle_response'):
                 result, status = recall_api.handle_response(response)
            else: # Fallback if using dummy
                 status = response.status_code
                 result = response.json() if status == 200 else {}


            if status != 200:
                print(f"Error fetching calendar events (status {status}): {json.dumps(result, indent=2)}")
                break # Stop pagination on error

            current_events = result.get('results', [])
            print(f"Fetched {len(current_events)} events from {next_url}")
            events.extend(current_events)

            # Get URL for the next page
            next_url = result.get('next')

        except requests.exceptions.RequestException as e:
            print(f"Network error fetching calendar events: {e}")
            break # Stop pagination on network error
        except Exception as e:
            print(f"Unexpected error fetching calendar events: {e}")
            break

    print(f"Total Recall events fetched for calendar {calendar_id}: {len(events)}")
    return events

def process_recall_events_for_sync(events: list[dict]) -> list[dict]:
    """Process Recall calendar events into a standard format needed for sync logic."""
    meetings = []
    for event in events:
        # Skip deleted events explicitly marked by Recall
        if event.get('is_deleted', False):
            continue

        meeting_url = extract_meeting_url(event) # Use utility function

        # Create a simplified meeting representation
        meeting_info = {
            'id': event.get('id'), # Recall's event ID is crucial
            'title': event.get('title', 'No Title'),
            'start_time': event.get('start_time'), # ISO 8601 format expected
            'end_time': event.get('end_time'),     # ISO 8601 format expected
            'meeting_url': meeting_url,
            'calendar_id': event.get('calendar_id'),
            'ical_uid': event.get('ical_uid'), # Useful for debugging/correlation
            'bot': event.get('bot'), # Info about any currently scheduled bot
            # Keep raw event data if needed for debugging or deeper logic
            # 'raw_data': event.get('raw', {})
        }
        # Filter out events without an ID, as they cannot be tracked
        if meeting_info['id']:
            meetings.append(meeting_info)
        else:
            print(f"Warning: Skipping Recall event due to missing ID: {event.get('title', 'No Title')}")

    return meetings


def create_calendar_integration(token_data: dict) -> str | None:
    """Create a calendar integration in Recall API using Google OAuth credentials."""
    # Ensure required fields are present in token_data and config
    required_oauth = ['client_id', 'client_secret', 'refresh_token']
    missing = [field for field in required_oauth if not token_data.get(field)]
    if missing:
        print(f"Error: Cannot create Recall calendar integration. Missing token data: {', '.join(missing)}")
        return None

    print("Attempting to create Recall calendar integration...")
    # Use the method from the imported RecallAPI instance

    response, status_code = recall_api.create_calendar(
        oauth_client_id=token_data['client_id'],
        oauth_client_secret=token_data['client_secret'],
        oauth_refresh_token=token_data['refresh_token'],
        platform="google_calendar" # Specify the platform
    )

    if status_code == 201 and response and 'id' in response:
        calendar_id = response['id']
        print(f"Recall calendar integration created successfully! Calendar ID: {calendar_id}")
        return calendar_id
    else:
        print(f"Failed to create calendar in Recall API. Status: {status_code}")
        print(f"Response: {json.dumps(response, indent=2)}")
        return None


def schedule_recall_bot(calendar_event_id: str, meeting_url: str) -> dict | None:
    """Schedule a Recall bot for a specific calendar event."""
    if not meeting_url:
        print(f"Skipping bot scheduling for event {calendar_event_id}: No meeting URL provided.")
        return None

    # Generate a unique key to prevent duplicate bot scheduling for the same event trigger
    # Using event ID + UUID ensures uniqueness even if called multiple times rapidly
    deduplication_key = f"event_{calendar_event_id}_{uuid.uuid4()}"

    bot_config = {
        "meeting_url": meeting_url,
        "bot_name": RECALL_BOT_NAME,
        "transcription_options": { # Example: Enable transcription
             "provider": "recall_ai"
        },
        "recording_mode": "speaker_view", # Or "gallery_view"
        "automatic_leave": {
            "everyone_left_timeout": 150 # Seconds after everyone leaves
        }
        # Add other bot configurations as needed
    }

    # Data payload for the Recall API v2 endpoint
    data = {
        "deduplication_key": deduplication_key,
        "bot_config": bot_config
    }

    url = f"{RECALL_API_BASE_URL}/calendar-events/{calendar_event_id}/bot/"

    print(f"Scheduling Recall bot for event {calendar_event_id} with URL: {meeting_url}")

    try:
        response = requests.post(url, headers=recall_api.get_headers(), json=data)
        # Use handle_response if available
        if hasattr(recall_api, 'handle_response'):
            result, status = recall_api.handle_response(response)
        else:
            status = response.status_code
            result = response.json() if 200 <= status < 300 else {}

        if 200 <= status < 300:
            # Check if 'bots' key exists and has content
            if result and 'bots' in result and isinstance(result['bots'], list) and len(result['bots']) > 0:
                 bot_info = result['bots'][0] # Assuming the first bot is the relevant one
                 print(f"Bot scheduled successfully for event {calendar_event_id}. Bot ID: {bot_info.get('bot_id')}")
                 # Return the relevant part (the bot info dict)
                 return bot_info
            else:
                 # Handle cases where API returns 2xx but maybe no bot info? (Unlikely but safe)
                 print(f"Bot scheduling for event {calendar_event_id} returned status {status}, but no bot info found in response.")
                 print(f"Response: {json.dumps(result, indent=2)}")
                 # Return None as we didn't get the expected bot info
                 return None

        else:
            print(f"Failed to schedule bot for event {calendar_event_id}. Status: {status}")
            print(f"Response: {json.dumps(result, indent=2)}")
            # Check for specific error messages if available
            if isinstance(result, dict) and "detail" in result:
                 print(f"Error detail: {result['detail']}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Network error scheduling bot for event {calendar_event_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error scheduling bot for event {calendar_event_id}: {e}")
        return None


def unschedule_recall_bot(calendar_event_id: str) -> bool:
    """Unschedule any existing Recall bot associated with a calendar event."""
    # Endpoint structure from original code
    url = f"{RECALL_API_BASE_URL}/calendar-events/{calendar_event_id}/bot/"

    print(f"Unscheduling Recall bot for event {calendar_event_id}...")

    try:
        response = requests.delete(url, headers=recall_api.get_headers())
        status = response.status_code

        if status == 204: # No Content - Successful deletion
            print(f"Bot unscheduled successfully for event {calendar_event_id}.")
            return True
        elif status == 404: # Not Found - Bot might have already finished or never existed
             print(f"No active bot found to unschedule for event {calendar_event_id} (status 404). Assuming success.")
             return True # Treat as success if the goal is no bot scheduled
        else:
             # Try to parse potential error message from response body
             error_detail = "No details available."
             try:
                  result = response.json()
                  error_detail = json.dumps(result, indent=2)
                  if isinstance(result, dict) and "detail" in result:
                      error_detail = result['detail']
             except json.JSONDecodeError:
                  error_detail = response.text # Use raw text if not JSON

             print(f"Failed to unschedule bot for event {calendar_event_id}. Status: {status}")
             print(f"Error detail: {error_detail}")
             return False

    except requests.exceptions.RequestException as e:
        print(f"Network error unscheduling bot for event {calendar_event_id}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error unscheduling bot for event {calendar_event_id}: {e}")
        return False


def check_and_process_finished_bots(user_id: str, user_data: dict) -> Tuple[int, int, bool]: # Added bool return for modified status
    """
    Checks Recall for finished bots relevant to the user, processes recordings
    (download, convert, upload), updates user_data, and cleans up.
    Returns (number_of_meetings_processed, number_of_orphaned_bots_removed, user_data_was_modified).
    """
    processed_count = 0
    removed_orphans_count = 0
    user_data_modified = False # Flag to track if save is needed

    # --- Identify Bots to Check ---
    bots_to_check = {} # { bot_id: meeting_id }
    bots_potentially_orphaned = set() # bot_ids for meetings marked removed long ago

    for meeting_id, bot_data in user_data.get('bots', {}).items():
        if bot_data and 'bot_id' in bot_data and not bot_data.get('audio_processed', False):
            bot_id = bot_data['bot_id']
            bots_to_check[bot_id] = meeting_id

            if bot_data.get('meeting_removed', False) and 'removed_at' in bot_data:
                try:
                    removed_time = datetime.fromisoformat(bot_data['removed_at'])
                    if (datetime.now(timezone.utc) - removed_time).total_seconds() > BOT_REMOVAL_CHECK_HOURS * 3600:
                        bots_potentially_orphaned.add(bot_id)
                except (ValueError, TypeError):
                    pass

    if not bots_to_check:
        return 0, 0, False # Nothing to do, data not modified

    print(f"Checking status for {len(bots_to_check)} bots for user {user_id}")

    # --- Get Finished Bot Status from Recall ---
    try:
        if not hasattr(recall_api, 'list_finished_bots'):
             print("Error: RecallAPI instance does not have 'list_finished_bots' method.")
             finished_bots_details = {}
        else:
             finished_bots_details = recall_api.list_finished_bots(list(bots_to_check.keys()))
    except Exception as e:
         print(f"Error calling recall_api.list_finished_bots: {e}")
         finished_bots_details = {}

    print(f"Found {len(finished_bots_details)} finished bots among those checked.")

    # --- Handle Potentially Orphaned Bots ---
    bots_to_remove_from_tracking = set()
    if bots_potentially_orphaned:
        for bot_id in bots_potentially_orphaned:
            if bot_id not in finished_bots_details:
                try:
                    print(f"Checking status of potentially orphaned bot {bot_id}...")
                    if not hasattr(recall_api, 'check_bot_status'):
                         print(f"Warning: Cannot check status of orphaned bot {bot_id}, RecallAPI dummy/missing method.")
                         continue
                    details, status_code = recall_api.check_bot_status(bot_id)
                    if status_code == 404 or (status_code != 200 and (not details or not details.get('video_url'))):
                         print(f"Orphaned bot {bot_id} is gone or errored (status {status_code}). Marking for removal.")
                         bots_to_remove_from_tracking.add(bot_id)
                    else:
                         print(f"Orphaned bot {bot_id} still exists (status {status_code}). Will keep checking.")
                except Exception as e:
                     print(f"Error checking status of orphaned bot {bot_id}: {e}")

    if bots_to_remove_from_tracking:
        meetings_to_remove_bot_entry = []
        for meeting_id, bot_data in user_data.get('bots', {}).items():
             if bot_data.get('bot_id') in bots_to_remove_from_tracking:
                  meetings_to_remove_bot_entry.append(meeting_id)

        for meeting_id in meetings_to_remove_bot_entry:
             if meeting_id in user_data.get('bots', {}):
                 removed_bot_id = user_data['bots'][meeting_id].get('bot_id', 'N/A')
                 print(f"Removing tracking entry for orphaned/gone bot {removed_bot_id} (meeting {meeting_id})")
                 del user_data['bots'][meeting_id]
                 removed_orphans_count += 1
                 user_data_modified = True

    # --- Process Finished Bots ---
    for bot_id, bot_details in finished_bots_details.items():
        meeting_id = bots_to_check.get(bot_id)
        if not meeting_id or meeting_id not in user_data.get('bots', {}):
            print(f"Warning: Finished bot {bot_id} has no corresponding meeting_id or entry in user_data. Skipping.")
            continue

        print(f"Processing finished bot {bot_id} for meeting {meeting_id}")

        # Define expected S3 paths and local temp paths using os.path.join
        s3_base_key = f"{user_id}/{meeting_id}"
        s3_audio_key = f"{s3_base_key}/recording.mp3"
        s3_meta_key = f"{s3_base_key}/metadata.json"
        # Use specific temp names (string paths)
        local_base_name = os.path.join(TEMP_FOLDER, f"{user_id}_{meeting_id}_{bot_id}")
        local_video_path = local_base_name + ".mp4"
        local_mp3_path = local_base_name + ".mp3"
        local_meta_path = local_base_name + ".json"

        # Check if already processed and uploaded
        if file_exists_in_s3(s3_audio_key) and file_exists_in_s3(s3_meta_key):
            print(f"Audio and metadata already exist in S3 for meeting {meeting_id}. Updating status.")
            s3_audio_url = f"s3://{S3_BUCKET}/{s3_audio_key}"
            s3_meta_url = f"s3://{S3_BUCKET}/{s3_meta_key}"
            participants = user_data['bots'][meeting_id].get('participants') or bot_details.get('meeting_participants_names', [])
        else:
            print(f"Processing recording for meeting {meeting_id}...")
            # 1. Download Video
            os.makedirs(TEMP_FOLDER, exist_ok=True)
            # recall_download_video expects base path *without* extension
            # Use os.path.join for the base path
            download_base_path = os.path.join(TEMP_FOLDER, bot_id)
            print(f"Attempting to download video for bot {bot_id} to base path {download_base_path}")

            try:
                 # Ensure recall_download_video is callable
                 if not callable(recall_download_video):
                      print("Error: recall_download_video is not callable (Import failure?). Skipping download.")
                      continue
                 downloaded_video_path, participants = recall_download_video(bot_id, download_base_path)
            except Exception as dl_error:
                 print(f"Error during recall_download_video call: {dl_error}")
                 downloaded_video_path = None
                 participants = []


            # Check if download succeeded *and* file exists
            if not downloaded_video_path or not os.path.exists(downloaded_video_path):
                print(f"Failed to download video for bot {bot_id} or file not found at {downloaded_video_path}. Skipping processing.")
                cleanup_temp_files(downloaded_video_path) # Clean up potential partial file
                continue
            print(f"Video downloaded to {downloaded_video_path}")

            # Rename downloaded file to our preferred local naming convention
            try:
                 # Use shutil.move for more robust renaming/moving across filesystems
                 shutil.move(downloaded_video_path, local_video_path)
                 print(f"Moved/Renamed downloaded video to {local_video_path}")
            except Exception as e: # Catch broader exceptions during move/rename
                 print(f"Error moving/renaming downloaded video file '{downloaded_video_path}' to '{local_video_path}': {e}. Attempting to continue with original path.")
                 # Fallback to using the original path if rename fails
                 local_video_path = downloaded_video_path


            # 2. Convert to MP3 (ensure input file exists)
            if not os.path.exists(local_video_path):
                print(f"Error: Video file path '{local_video_path}' does not exist before conversion. Skipping.")
                continue

            converted_mp3_path = convert_to_mp3(local_video_path)
            if not converted_mp3_path:
                print(f"Failed to convert video to MP3 for meeting {meeting_id}. Skipping upload.")
                cleanup_temp_files(local_video_path) # Clean up downloaded video
                continue
            local_mp3_path = converted_mp3_path

            # 3. Create Metadata File
            metadata = {
                'meeting_id': meeting_id, 'bot_id': bot_id, 'user_id': user_id,
                'title': bot_details.get('meeting_title') or user_data['bots'][meeting_id].get('title', 'Meeting Recording'),
                'participants': participants,
                'start_time': bot_details.get('start_time'), 'end_time': bot_details.get('end_time'),
                'recall_bot_details': bot_details,
                'processing_timestamp_utc': datetime.now(timezone.utc).isoformat()
            }
            if not save_meeting_metadata(metadata, local_meta_path):
                print(f"Failed to save metadata for meeting {meeting_id}. Skipping upload.")
                cleanup_temp_files(local_video_path, local_mp3_path)
                continue

            # 4. Upload MP3 and Metadata to S3
            s3_audio_url = upload_to_s3(local_mp3_path, s3_audio_key, content_type='audio/mpeg')
            s3_meta_url = upload_to_s3(local_meta_path, s3_meta_key, content_type='application/json')

            # 5. Clean up local files AFTER successful upload
            if s3_audio_url and s3_meta_url:
                print(f"Uploads successful for meeting {meeting_id}.")
                cleanup_temp_files(local_video_path, local_mp3_path, local_meta_path)
            else:
                print(f"Failed to upload one or both files to S3 for meeting {meeting_id}. Local files kept for retry.")
                continue # Skip updating user data for this meeting

        # --- Update User Data ---
        user_data.setdefault('bots', {}).setdefault(meeting_id, {}) # Ensure meeting_id entry exists
        user_data['bots'][meeting_id].update({
            'audio_processed': True,
            'audio_url': s3_audio_url,
            'metadata_url': s3_meta_url,
            'participants': participants, # Store participants list
            'processed_at': datetime.now(timezone.utc).isoformat()
        })
        processed_count += 1
        user_data_modified = True
        print(f"Successfully marked meeting {meeting_id} as processed.")


    print(f"Finished processing bots for user {user_id}. Processed: {processed_count}, Orphans Removed: {removed_orphans_count}")
    return processed_count, removed_orphans_count, user_data_modified
