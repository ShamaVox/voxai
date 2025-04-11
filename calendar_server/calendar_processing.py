import os
from datetime import datetime, timezone
import traceback

import data_manager
import recall_adapter
from oauth import refresh_token_if_needed
from utils import find_meeting_changes, is_meeting_in_past

def process_user_calendar(user_id: str, token_data: dict) -> bool:
    """
    Processes a single user's calendar:
    1. Refreshes Google OAuth token if needed.
    2. Ensures Recall calendar integration exists.
    3. Fetches upcoming events from Recall.
    4. Compares with previously stored events to find changes.
    5. Schedules/unschedules Recall bots based on changes.
    6. Updates and saves the user's data file.
    Returns True if successful, False otherwise.
    """
    print(f"\n--- Processing calendar for user: {user_id} ---")

    # --- 1. Refresh Google Token ---
    # Crucial step: Ensure Recall can access the calendar via Google
    # Refreshing the Google token might be needed *before* interacting with Recall,
    # especially if Recall uses it directly or needs it refreshed for its own sync.
    print("Checking/Refreshing Google OAuth token...")
    google_creds = refresh_token_if_needed(user_id)
    if google_creds is None:
        print(f"Cannot process calendar for {user_id}: Failed to get valid Google credentials.")
        # No point continuing if Google access fails
        return False
    print("Google OAuth token is valid.")
    # Update token_data in memory with potentially refreshed credentials for Recall
    token_data['token'] = google_creds.token
    if google_creds.refresh_token: # Refresh token might change
         token_data['refresh_token'] = google_creds.refresh_token
    token_data['expiry'] = google_creds.expiry.isoformat().replace('+00:00', 'Z') if google_creds.expiry else None


    # --- 2. Load User Data & Ensure Recall Calendar Integration ---
    user_data = data_manager.load_user_data(user_id)
    recall_calendar_id = user_data.get('recall_calendar_id')
    user_data_modified = False # Track if we need to save later

    if not recall_calendar_id:
        print(f"No Recall Calendar ID found for {user_id}. Attempting to create one...")
        # Pass the potentially refreshed token_data
        recall_calendar_id = recall_adapter.create_calendar_integration(token_data)
        if recall_calendar_id:
            user_data['recall_calendar_id'] = recall_calendar_id
            user_data_modified = True # Need to save the new ID
            print(f"Recall Calendar ID created and saved: {recall_calendar_id}")
        else:
            print(f"Failed to create Recall calendar integration for {user_id}. Aborting processing.")
            # Save any potential token refresh updates even if calendar creation failed
            data_manager.save_token_data(user_id, token_data)
            return False # Cannot proceed without a Recall calendar ID
    else:
        print(f"Using existing Recall Calendar ID: {recall_calendar_id}")

    # --- 3. Fetch Upcoming Events from Recall ---
    try:
        print(f"Fetching upcoming events from Recall for calendar {recall_calendar_id}...")
        current_recall_events = recall_adapter.list_calendar_events(recall_calendar_id)
        # Process into our standard meeting format
        current_meetings = recall_adapter.process_recall_events_for_sync(current_recall_events)
        print(f"Found {len(current_meetings)} upcoming meetings in Recall.")
    except Exception as e:
        print(f"Error fetching or processing Recall events for {user_id}: {e}")
        traceback.print_exc()
        # Save user data if modified (e.g., new calendar ID) before returning
        if user_data_modified:
            data_manager.save_user_data(user_id, user_data)
        return False # Cannot proceed without event data

    # --- 4. Compare with Previous State & Find Changes ---
    old_meetings = user_data.get('meetings', [])
    print(f"Comparing {len(current_meetings)} current meetings with {len(old_meetings)} previously stored meetings.")
    changes = find_meeting_changes(old_meetings, current_meetings)
    print(f"Changes detected: {len(changes['new'])} new, {len(changes['changed'])} changed, {len(changes['removed'])} removed.")

    # Ensure 'bots' dictionary exists
    user_data.setdefault('bots', {})

    # --- 5. Process Changes ---

    # Handle NEW meetings
    for meeting in changes['new']:
        meeting_id = meeting['id']
        meeting_url = meeting.get('meeting_url')
        print(f"Processing NEW meeting: {meeting_id} - {meeting.get('title', 'No Title')}")
        if meeting_url:
            print(f"  Scheduling bot for URL: {meeting_url}")
            bot_info = recall_adapter.schedule_recall_bot(meeting_id, meeting_url)
            if bot_info and 'bot_id' in bot_info:
                user_data['bots'][meeting_id] = {
                    'bot_id': bot_info['bot_id'],
                    'meeting_url': meeting_url,
                    'title': meeting.get('title'), # Store title for context
                    'start_time': meeting.get('start_time'),
                    'end_time': meeting.get('end_time'),
                    'scheduled_at': datetime.now(timezone.utc).isoformat(),
                    'audio_processed': False, # Initialize status fields
                    'meeting_removed': False
                }
                user_data_modified = True
            else:
                print(f"  Failed to schedule bot for new meeting {meeting_id}.")
        else:
            print(f"  Skipping bot scheduling for new meeting {meeting_id}: No meeting URL found.")

    # Handle CHANGED meetings (e.g., time, potentially URL)
    for meeting in changes['changed']:
        meeting_id = meeting['id']
        new_meeting_url = meeting.get('meeting_url')
        old_bot_info = user_data['bots'].get(meeting_id)
        print(f"Processing CHANGED meeting: {meeting_id} - {meeting.get('title', 'No Title')}")

        # Always attempt to unschedule any existing bot first for simplicity.
        # Recall might handle rescheduling internally, but explicit unschedule/schedule is safer.
        if old_bot_info and 'bot_id' in old_bot_info:
            print(f"  Unscheduling existing bot {old_bot_info['bot_id']} due to meeting change.")
            unschedule_success = recall_adapter.unschedule_recall_bot(meeting_id)
            if not unschedule_success:
                 print(f"  Warning: Failed to unschedule existing bot for changed meeting {meeting_id}. Proceeding with scheduling attempt.")
            # Remove or update the bot entry regardless of unschedule success to reflect the change attempt
            # If rescheduling fails, we don't want the old bot info lingering incorrectly.
            if meeting_id in user_data['bots']: del user_data['bots'][meeting_id]
            user_data_modified = True


        # Schedule a new bot if there's a valid URL
        if new_meeting_url:
            print(f"  Scheduling new/updated bot for URL: {new_meeting_url}")
            bot_info = recall_adapter.schedule_recall_bot(meeting_id, new_meeting_url)
            if bot_info and 'bot_id' in bot_info:
                user_data['bots'][meeting_id] = {
                    'bot_id': bot_info['bot_id'],
                    'meeting_url': new_meeting_url,
                    'title': meeting.get('title'),
                    'start_time': meeting.get('start_time'),
                    'end_time': meeting.get('end_time'),
                    'scheduled_at': datetime.now(timezone.utc).isoformat(),
                    'audio_processed': False,
                    'meeting_removed': False
                }
                user_data_modified = True
                print(f"  Successfully scheduled new bot {bot_info['bot_id']} for changed meeting.")
            else:
                print(f"  Failed to schedule bot for changed meeting {meeting_id}.")
                # Ensure no incorrect bot entry exists if scheduling failed after unscheduling
                if meeting_id in user_data['bots']: del user_data['bots'][meeting_id]
                user_data_modified = True
        else:
            print(f"  Skipping bot scheduling for changed meeting {meeting_id}: No meeting URL found.")
            # Ensure no incorrect bot entry exists if URL was removed
            if meeting_id in user_data['bots']: del user_data['bots'][meeting_id]
            user_data_modified = True

    # Handle REMOVED meetings
    for meeting_id in changes['removed']:
        print(f"Processing REMOVED meeting ID: {meeting_id}")
        if meeting_id in user_data['bots']:
            bot_data = user_data['bots'][meeting_id]
            bot_id = bot_data.get('bot_id')

            # Find the original meeting details from the old list to check its end time
            original_meeting = next((m for m in old_meetings if m['id'] == meeting_id), None)

            # If the meeting was in the past OR already processed, don't unschedule. Mark for check.
            if bot_data.get('audio_processed') or (original_meeting and is_meeting_in_past(original_meeting)):
                print(f"  Meeting {meeting_id} removed from calendar, but it's in the past or already processed.")
                # Mark as removed so the finished bot check knows, but keep the entry
                if not bot_data.get('meeting_removed'): # Only mark if not already marked
                     user_data['bots'][meeting_id]['meeting_removed'] = True
                     user_data['bots'][meeting_id]['removed_at'] = datetime.now(timezone.utc).isoformat()
                     user_data_modified = True
                     print(f"  Marked meeting {meeting_id} as removed in data for future cleanup.")
            else:
                # Meeting is in the future and not processed, unschedule the bot.
                print(f"  Meeting {meeting_id} is upcoming/current. Unscheduling bot {bot_id}.")
                if bot_id:
                    recall_adapter.unschedule_recall_bot(meeting_id) # Attempt unschedule
                # Remove the bot entry from tracking entirely
                del user_data['bots'][meeting_id]
                user_data_modified = True
                print(f"  Removed bot tracking for meeting {meeting_id}.")
        else:
             print(f"  Meeting {meeting_id} removed, but no associated bot was found in tracking data.")

    # --- 6. Update and Save User Data ---
    user_data['meetings'] = current_meetings # Store the latest list of meetings for next comparison
    user_data['last_updated'] = datetime.now(timezone.utc).isoformat()
    data_manager.save_user_data(user_id, user_data)
    print(f"User data updated and saved for {user_id}.")

    print(f"--- Finished processing calendar for user: {user_id} ---")
    return True


def check_all_calendars():
    """
    Iterates through all known users (based on token files), processes their
    calendars, and then checks for/processes finished recordings for all users.
    """
    print(f"\n=== Starting Full Calendar and Recording Check @ {datetime.now(timezone.utc).isoformat()} ===")

    token_files = data_manager.get_token_files()
    print(f"Found {len(token_files)} user token files.")

    successful_users = 0
    failed_users = 0

    # --- Process each user's calendar individually ---
    for token_file in token_files:
        user_id = os.path.splitext(token_file)[0]
        try:
            token_data = data_manager.load_token_data(token_file)
            if not token_data:
                 print(f"Skipping user {user_id}: Could not load token data.")
                 failed_users += 1
                 continue

            success = process_user_calendar(user_id, token_data) # token_data might be updated internally
            if success:
                successful_users += 1
            else:
                failed_users += 1
                print(f"Processing failed for user {user_id}.")

        except Exception as e:
            print(f"!!! Unhandled error processing user {user_id}: {str(e)} !!!")
            traceback.print_exc()
            failed_users += 1

    print(f"\n--- Calendar Sync Summary ---")
    print(f"Successfully processed: {successful_users} users")
    print(f"Failed to process: {failed_users} users")

    # --- Check and process finished recordings across ALL users ---
    # This is done after all calendar syncs to catch recordings from meetings
    # that might have just finished or were removed during the sync phase.
    print("\n--- Starting Finished Recordings Check ---")
    total_processed_recordings = 0
    total_removed_orphans = 0

    # Reload token files in case authentication added a new user during the loop
    token_files = data_manager.get_token_files()

    for token_file in token_files:
         user_id = os.path.splitext(token_file)[0]
         print(f"Checking finished recordings for user: {user_id}")
         try:
             # Load the latest user data, which might have been modified by process_user_calendar
             user_data = data_manager.load_user_data(user_id)
             processed_count, removed_count, data_modified = recall_adapter.check_and_process_finished_bots(user_id, user_data)
             total_processed_recordings += processed_count
             total_removed_orphans += removed_count

             # Save user_data ONLY if check_and_process_finished_bots reported changes
             if data_modified:
                  print(f"Saving updated user data for {user_id} after recording check.")
                  data_manager.save_user_data(user_id, user_data)

         except Exception as e:
              print(f"!!! Error checking finished recordings for user {user_id}: {str(e)} !!!")
              traceback.print_exc()

    print(f"\n--- Finished Recordings Summary ---")
    print(f"Total recordings processed and uploaded: {total_processed_recordings}")
    print(f"Total orphaned/gone bots removed from tracking: {total_removed_orphans}")

    print(f"=== Full Check Cycle Completed @ {datetime.now(timezone.utc).isoformat()} ===")
    return True # Indicate the overall cycle attempted to run
