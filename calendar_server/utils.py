import json
import os
from datetime import datetime, timezone, timedelta 
from pathlib import Path

def extract_meeting_url(event: dict) -> str:
    """Extract meeting URL from a Recall calendar event."""
    meeting_url = event.get('meeting_url', '')

    # If no meeting URL found, check the event details (raw Google Calendar data)
    if not meeting_url and 'raw' in event:
        raw_event = event['raw']
        # Check Google Calendar's conferenceData
        if 'conferenceData' in raw_event:
            conf_data = raw_event['conferenceData']
            if 'entryPoints' in conf_data:
                # First pass: prioritize video links
                for entry in conf_data['entryPoints']:
                    if entry.get('entryPointType') == 'video' and entry.get('uri'):
                        meeting_url = entry.get('uri')
                        break # Found the best type, stop

                # Second pass (fallback): find any other usable URI if no video link found
                # Preferring http/https urls over tel: or others if possible
                if not meeting_url:
                    potential_fallback_url = ''
                    for entry in conf_data['entryPoints']:
                        uri = entry.get('uri')
                        if uri:
                             # Keep the last seen URI as a fallback
                             potential_fallback_url = uri
                             # If it looks like a web meeting link, prefer it and stop
                             if isinstance(uri, str) and (uri.startswith('http://') or uri.startswith('https://')):
                                  meeting_url = uri
                                  break # Found a good web link, stop
                    # If we iterated through all and only found non-http links, use the last one found
                    if not meeting_url:
                         meeting_url = potential_fallback_url

        # Try 'location' field as a final fallback
        if not meeting_url and 'location' in raw_event:
            location = raw_event.get('location', '')
            if location and isinstance(location, str): # Ensure location is a string
                # Simple pattern matching for common meeting platforms
                for word in location.split():
                    normalized_word = word.lower()
                    if any(domain in normalized_word for domain in ['zoom.us', 'teams.microsoft.com', 'meet.google.com']):
                        # Basic validation to ensure it looks like a URL
                        if normalized_word.startswith('http://') or normalized_word.startswith('https://'):
                             meeting_url = word # Keep original casing
                             break

    # Ensure always returning string, default to empty string
    return meeting_url if isinstance(meeting_url, str) else ''

def find_meeting_changes(old_meetings: list[dict], new_meetings: list[dict]) -> dict:
    """
    Compare old and new meetings (from Recall) to find additions, changes, and removals.
    Compares based on meeting 'id' and 'start_time'/'end_time'.
    """
    old_meetings_dict = {m['id']: m for m in old_meetings}
    new_meetings_dict = {m['id']: m for m in new_meetings}

    old_ids = set(old_meetings_dict.keys())
    new_ids = set(new_meetings_dict.keys())

    new_meeting_ids = new_ids - old_ids
    removed_meeting_ids = old_ids - new_ids
    common_ids = old_ids & new_ids

    changed_meeting_ids = set()
    for meeting_id in common_ids:
        old_meeting = old_meetings_dict[meeting_id]
        new_meeting = new_meetings_dict[meeting_id]

        # Key fields to check for changes that warrant rescheduling
        fields_to_check = ['start_time', 'end_time', 'meeting_url']
        changed = False
        for field in fields_to_check:
             # Use .get() to handle potentially missing keys gracefully
            if old_meeting.get(field) != new_meeting.get(field):
                changed = True
                break
        if changed:
             changed_meeting_ids.add(meeting_id)

    return {
        'new': [new_meetings_dict[id] for id in new_meeting_ids],
        'changed': [new_meetings_dict[id] for id in changed_meeting_ids],
        'removed': list(removed_meeting_ids) # List of IDs that were removed
    }

def parse_iso_datetime(dt_str: str | None) -> datetime | None:
    """Safely parse ISO 8601 datetime strings, handling potential Z suffix."""
    if not dt_str:
        return None
    try:
        # Replace 'Z' with '+00:00' for Python compatibility if necessary
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        print(f"Warning: Could not parse datetime string: {dt_str}")
        return None

def is_meeting_in_past(meeting: dict) -> bool:
    """Check if a meeting's end time is in the past."""
    end_time_str = meeting.get('end_time')
    end_time = parse_iso_datetime(end_time_str)
    if end_time:
        # Ensure comparison is timezone-aware
        now_utc = datetime.now(timezone.utc)
        # If end_time is naive, assume UTC for comparison (or handle based on expected timezone)
        if end_time.tzinfo is None:
            # This assumes naive datetimes from source should be treated as UTC. Adjust if needed.
            print(f"Warning: Assuming UTC for naive end_time {end_time_str}")
            return end_time.replace(tzinfo=timezone.utc) < now_utc
        else:
            return end_time < now_utc
    # If no end time, assume it's not definitively in the past for safety
    return False

def save_meeting_metadata(meeting_data: dict, output_path: str) -> bool:
    """Save meeting metadata to a JSON file."""
    try:
        # Ensure output_path is a string for os.path.dirname
        output_dir = os.path.dirname(str(output_path))
        if output_dir: # Avoid trying to create '' if path is just a filename
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(meeting_data, f, indent=2)
        print(f"Metadata saved to {output_path}")
        return True
    except Exception as e:
        print(f"Error saving meeting metadata to {output_path}: {str(e)}")
        return False
