import pytest
import os # Import os
from datetime import datetime, timedelta, timezone
# Removed Path import
from utils import (
    extract_meeting_url,
    find_meeting_changes,
    parse_iso_datetime,
    is_meeting_in_past,
    save_meeting_metadata
)

# --- Test extract_meeting_url ---

@pytest.mark.parametrize("event, expected_url", [
    # Case 1: URL directly in event
    ({"meeting_url": "https://zoom.us/j/123", "raw": {}}, "https://zoom.us/j/123"),
    # Case 2: Google Meet URL in raw conferenceData (video entry point)
    ({"raw": {"conferenceData": {"entryPoints": [{"entryPointType": "video", "uri": "https://meet.google.com/abc-def-ghi"}]}}}, "https://meet.google.com/abc-def-ghi"),
    # Case 3: Google Meet URL preferred over phone URI in fallback
    ({"raw": {"conferenceData": {"entryPoints": [{"entryPointType": "phone", "uri": "tel:+1..."}, {"entryPointType": "more", "uri": "https://meet.google.com/abc-xyz"}]}}}, "https://meet.google.com/abc-xyz"), # http preferred
    # Case 4: Zoom URL in location field
    ({"raw": {"location": "My Office\nJoin here: https://zoom.us/j/456?pwd=abc"}}, "https://zoom.us/j/456?pwd=abc"),
    # Case 5: Teams URL in location field
    ({"raw": {"location": "https://teams.microsoft.com/l/meetup-join/..."}}, "https://teams.microsoft.com/l/meetup-join/..."),
    # Case 6: URL in event takes precedence over raw data
    ({"meeting_url": "https://explicit.com/meeting", "raw": {"location": "https://implicit.com/meeting"}}, "https://explicit.com/meeting"),
    # Case 7: No URL found
    ({"raw": {"location": "Conference Room A"}}, ""),
    # Case 8: Empty event
    ({}, ""),
    # Case 9: Malformed conferenceData
    ({"raw": {"conferenceData": {"entryPoints": [{"type": "video"}]}}}, ""), # Missing uri
    # Case 10: Only phone URI available (should be returned as last resort)
    ({"raw": {"conferenceData": {"entryPoints": [{"entryPointType": "phone", "uri": "tel:+1..."}]}}}, "tel:+1..."),
])
def test_extract_meeting_url(event, expected_url):
    assert extract_meeting_url(event) == expected_url

# --- Test find_meeting_changes ---

BASE_MEETING_1 = {'id': '1', 'start_time': '2023-01-01T10:00:00Z', 'end_time': '2023-01-01T11:00:00Z', 'meeting_url': 'url1'}
BASE_MEETING_2 = {'id': '2', 'start_time': '2023-01-01T12:00:00Z', 'end_time': '2023-01-01T13:00:00Z', 'meeting_url': 'url2'}

def test_find_meeting_changes_no_change():
    old = [BASE_MEETING_1, BASE_MEETING_2]
    new = [BASE_MEETING_1, BASE_MEETING_2]
    changes = find_meeting_changes(old, new)
    assert not changes['new']
    assert not changes['changed']
    assert not changes['removed']

def test_find_meeting_changes_new_meeting():
    old = [BASE_MEETING_1]
    new = [BASE_MEETING_1, BASE_MEETING_2]
    changes = find_meeting_changes(old, new)
    assert changes['new'] == [BASE_MEETING_2]
    assert not changes['changed']
    assert not changes['removed']

def test_find_meeting_changes_removed_meeting():
    old = [BASE_MEETING_1, BASE_MEETING_2]
    new = [BASE_MEETING_1]
    changes = find_meeting_changes(old, new)
    assert not changes['new']
    assert not changes['changed']
    assert changes['removed'] == ['2'] # Should be list of IDs

def test_find_meeting_changes_changed_time():
    old = [BASE_MEETING_1]
    changed_meeting_1 = {**BASE_MEETING_1, 'start_time': '2023-01-01T10:05:00Z'}
    new = [changed_meeting_1]
    changes = find_meeting_changes(old, new)
    assert not changes['new']
    assert changes['changed'] == [changed_meeting_1]
    assert not changes['removed']

def test_find_meeting_changes_changed_url():
    old = [BASE_MEETING_1]
    changed_meeting_1 = {**BASE_MEETING_1, 'meeting_url': 'url1_updated'}
    new = [changed_meeting_1]
    changes = find_meeting_changes(old, new)
    assert not changes['new']
    assert changes['changed'] == [changed_meeting_1]
    assert not changes['removed']

def test_find_meeting_changes_combination():
    old = [BASE_MEETING_1, {'id': '3', 'start_time': '2023-01-02T10:00:00Z', 'end_time': '2023-01-02T11:00:00Z', 'meeting_url': 'url3'}] # 1 exists, 3 removed
    changed_meeting_1 = {**BASE_MEETING_1, 'end_time': '2023-01-01T11:05:00Z'} # 1 changed
    new = [changed_meeting_1, BASE_MEETING_2] # 1 changed, 2 added
    changes = find_meeting_changes(old, new)
    assert changes['new'] == [BASE_MEETING_2]
    assert changes['changed'] == [changed_meeting_1]
    assert changes['removed'] == ['3']

# --- Test parse_iso_datetime ---

def test_parse_iso_datetime():
    assert parse_iso_datetime("2023-10-27T10:00:00Z") == datetime(2023, 10, 27, 10, 0, 0, tzinfo=timezone.utc)
    assert parse_iso_datetime("2023-10-27T10:00:00+00:00") == datetime(2023, 10, 27, 10, 0, 0, tzinfo=timezone.utc)
    assert parse_iso_datetime("2023-10-27T12:00:00+02:00") == datetime(2023, 10, 27, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    assert parse_iso_datetime("invalid-date") is None
    assert parse_iso_datetime(None) is None

# --- Test save_meeting_metadata ---
def test_save_meeting_metadata(tmp_path):
    meta_data = {"id": "meeting1", "title": "Test Meeting", "participants": ["A", "B"]}
    # Use os.path.join for path construction
    output_dir = os.path.join(str(tmp_path), "subdir")
    output_file = os.path.join(output_dir, "meeting1_meta.json")

    # Pass path as string, as expected by the function
    success = save_meeting_metadata(meta_data, output_file)

    assert success is True
    assert os.path.isfile(output_file)
    with open(output_file, 'r') as f:
        import json
        saved_data = json.load(f)
        assert saved_data == meta_data
    # Check directory creation using os.path
    assert os.path.isdir(output_dir)

def test_save_meeting_metadata_failure(mocker):
    # Simulate an IOError during file writing
    mocker.patch("builtins.open", side_effect=IOError("Disk full"))
    meta_data = {"id": "meeting2"}
    # Path doesn't matter much here as open is mocked
    success = save_meeting_metadata(meta_data, "/fake/path/meta.json")
    assert success is False
