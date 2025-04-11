import pytest
import requests
import json
import os # Import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
# Removed Path import
import subprocess # Import subprocess

import recall_adapter
import data_manager
# Get paths as strings from fixture patching config
from config import RECALL_API_BASE_URL, TEMP_FOLDER, S3_BUCKET, BOT_REMOVAL_CHECK_HOURS
from utils import parse_iso_datetime

# Use fixtures from conftest.py: temp_folders, mock_recall_api, mock_boto3_s3, mock_subprocess

# Sample data for mocking API responses
SAMPLE_EVENT_1 = {
    "id": "evt_1", "title": "Meeting 1", "start_time": "2024-01-10T10:00:00Z",
    "end_time": "2024-01-10T11:00:00Z", "calendar_id": "cal_123",
    "meeting_url": "https://zoom.us/j/111", "bot": None, "is_deleted": False
}
SAMPLE_EVENT_2 = {
    "id": "evt_2", "title": "Meeting 2", "start_time": "2024-01-10T14:00:00Z",
    "end_time": "2024-01-10T15:00:00Z", "calendar_id": "cal_123",
    "meeting_url": "https://meet.google.com/abc", "bot": {"bot_id": "bot_xyz", "status": "scheduled"}, "is_deleted": False
}
SAMPLE_DELETED_EVENT = {
    "id": "evt_3", "title": "Deleted Meeting", "start_time": "2024-01-10T16:00:00Z",
    "end_time": "2024-01-10T17:00:00Z", "calendar_id": "cal_123",
     "meeting_url": "https://zoom.us/j/333", "bot": None, "is_deleted": True
}

# --- Test list_calendar_events ---

@pytest.mark.usefixtures("freezer") # Add fixture marker
@patch('requests.get')
def test_list_calendar_events_single_page(mock_get, mock_recall_api, freezer): # Add freezer arg
    """Test fetching events when there's only one page."""
    freezer.move_to('2024-01-10T09:00:00Z')
    calendar_id = "cal_123"
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "count": 2, "next": None, "previous": None,
        "results": [SAMPLE_EVENT_1, SAMPLE_EVENT_2]
    }
    mock_get.return_value = mock_response
    # Mock handle_response to just pass through
    mock_recall_api.handle_response = lambda r: (r.json(), r.status_code)


    events = recall_adapter.list_calendar_events(calendar_id)

    assert len(events) == 2
    assert events[0]['id'] == 'evt_1'
    assert events[1]['id'] == 'evt_2'
    mock_get.assert_called_once()
    call_url = mock_get.call_args[0][0]
    assert f"calendar_id={calendar_id}" in call_url
    assert "start_time__gte=2024-01-10T09:00:00Z" in call_url
    assert "start_time__lte=2024-01-17T09:00:00Z" in call_url # 7 days ahead
    mock_recall_api.get_headers.assert_called_once()

@patch('requests.get')
def test_list_calendar_events_multiple_pages(mock_get, mock_recall_api):
    """Test fetching events with pagination."""
    calendar_id = "cal_456"
    # Construct more specific URLs for mocking side_effect
    base_query_pattern = f"?calendar_id={calendar_id}&start_time__gte=" # Start of query
    page1_url_pattern = f"{RECALL_API_BASE_URL}/calendar-events/" # Contains base_query implicitly
    page2_url = f"{RECALL_API_BASE_URL}/calendar-events/page2/"

    # Mock response for page 1
    mock_response1 = MagicMock(spec=requests.Response)
    mock_response1.status_code = 200
    mock_response1.json.return_value = {
        "count": 3, "next": page2_url, "previous": None, "results": [SAMPLE_EVENT_1]
    }
    # Mock response for page 2
    mock_response2 = MagicMock(spec=requests.Response)
    mock_response2.status_code = 200
    mock_response2.json.return_value = {
        "count": 3, "next": None, "previous": "some_prev_url", "results": [SAMPLE_EVENT_2, SAMPLE_DELETED_EVENT]
    }

    # Configure requests.get to return different responses based on URL
    def get_side_effect(url, headers):
        if "page2" in url:
            return mock_response2
        # Check if it's the initial request (contains the base query pattern)
        elif base_query_pattern in url and page1_url_pattern in url:
             return mock_response1
        else:
             pytest.fail(f"Unexpected URL requested: {url}") # Fail test if URL doesn't match
             return None # Should not be reached

    mock_get.side_effect = get_side_effect
    # Mock handle_response to just pass through
    mock_recall_api.handle_response = lambda r: (r.json(), r.status_code)


    events = recall_adapter.list_calendar_events(calendar_id)

    assert len(events) == 3
    assert events[0]['id'] == 'evt_1'
    assert events[1]['id'] == 'evt_2'
    assert events[2]['id'] == 'evt_3'
    assert mock_get.call_count == 2
    # Check headers were retrieved for each call
    assert mock_recall_api.get_headers.call_count == 2

@patch('requests.get')
def test_list_calendar_events_api_error(mock_get, mock_recall_api):
    """Test handling of API error during event fetching."""
    calendar_id = "cal_err"
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 500
    mock_response.json.return_value = {"detail": "Internal server error"}
    mock_get.return_value = mock_response
    # Make handle_response simulate error status
    mock_recall_api.handle_response = lambda r: (r.json(), r.status_code)

    events = recall_adapter.list_calendar_events(calendar_id)

    assert len(events) == 0 # Should return empty list on error
    mock_get.assert_called_once()

# --- Test process_recall_events_for_sync ---

def test_process_recall_events_for_sync():
    raw_events = [SAMPLE_EVENT_1, SAMPLE_EVENT_2, SAMPLE_DELETED_EVENT]
    processed = recall_adapter.process_recall_events_for_sync(raw_events)

    assert len(processed) == 2 # Deleted event should be filtered out
    assert processed[0]['id'] == SAMPLE_EVENT_1['id']
    assert processed[0]['meeting_url'] == SAMPLE_EVENT_1['meeting_url']
    assert 'raw_data' not in processed[0] # Raw data is not included by default

    assert processed[1]['id'] == SAMPLE_EVENT_2['id']
    assert processed[1]['meeting_url'] == SAMPLE_EVENT_2['meeting_url']
    assert processed[1]['bot'] == SAMPLE_EVENT_2['bot']

def test_process_recall_events_extracts_url():
    """Check that URL extraction is used."""
    event_no_url_field = {
         "id": "evt_4", "title": "Needs Extraction", "start_time": "2024-01-10T18:00:00Z",
         "end_time": "2024-01-10T19:00:00Z", "calendar_id": "cal_123",
         "raw": {"location": "Join here: https://zoom.us/j/444"}, "bot": None, "is_deleted": False
    }
    processed = recall_adapter.process_recall_events_for_sync([event_no_url_field])
    assert len(processed) == 1
    assert processed[0]['meeting_url'] == "https://zoom.us/j/444"

# --- Test create_calendar_integration ---

def test_create_calendar_integration_success(mock_recall_api):
    token_data = {"client_id": "cid", "client_secret": "csec", "refresh_token": "rtok"}
    # mock_recall_api fixture already mocks create_calendar for success
    calendar_id = recall_adapter.create_calendar_integration(token_data)

    assert calendar_id == "cal_12345"
    mock_recall_api.create_calendar.assert_called_once_with(
        oauth_client_id="cid",
        oauth_client_secret="csec",
        oauth_refresh_token="rtok",
        platform="google_calendar"
    )

def test_create_calendar_integration_failure(mock_recall_api):
    token_data = {"client_id": "cid", "client_secret": "csec", "refresh_token": "rtok"}
    # Simulate API failure
    mock_recall_api.create_calendar.return_value = ({"detail": "Invalid credentials"}, 400)

    calendar_id = recall_adapter.create_calendar_integration(token_data)
    assert calendar_id is None
    mock_recall_api.create_calendar.assert_called_once()

def test_create_calendar_integration_missing_token_data(mock_recall_api):
    token_data = {"client_id": "cid"} # Missing secret and refresh token
    calendar_id = recall_adapter.create_calendar_integration(token_data)
    assert calendar_id is None
    mock_recall_api.create_calendar.assert_not_called()

# --- Test schedule_recall_bot ---

@patch('requests.post')
def test_schedule_recall_bot_success(mock_post, mock_recall_api):
    event_id = "evt_sched_1"
    meeting_url = "https://zoom.us/j/sched"
    expected_bot_id = "bot_sched_abc"
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 201
    # Simulate Recall API response structure
    response_payload = {
        "deduplication_key": "some_key",
        "bots": [{"bot_id": expected_bot_id, "status": "pending"}]
    }
    mock_response.json.return_value = response_payload
    mock_post.return_value = mock_response

    # Override handle_response on the mocked API instance for this test
    mock_recall_api.handle_response = lambda r: (r.json(), r.status_code)
    # Reset mock before calling function
    mock_recall_api.get_headers.reset_mock()

    result = recall_adapter.schedule_recall_bot(event_id, meeting_url)

    assert result is not None
    assert result['bot_id'] == expected_bot_id
    mock_post.assert_called_once()
    call_url = mock_post.call_args[0][0]
    call_json = mock_post.call_args[1]['json']
    assert call_url == f"{RECALL_API_BASE_URL}/calendar-events/{event_id}/bot/"
    assert call_json['bot_config']['meeting_url'] == meeting_url
    assert call_json['bot_config']['bot_name'] == recall_adapter.RECALL_BOT_NAME
    assert "deduplication_key" in call_json
    assert call_json['deduplication_key'].startswith(f"event_{event_id}_")
    mock_recall_api.get_headers.assert_called_once() # Should be called once for the POST

@patch('requests.post')
def test_schedule_recall_bot_failure(mock_post, mock_recall_api):
    event_id = "evt_sched_fail"
    meeting_url = "https://zoom.us/j/fail"
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 400
    mock_response.json.return_value = {"detail": "Invalid meeting URL"}
    mock_post.return_value = mock_response
    mock_recall_api.handle_response = lambda r: (r.json(), r.status_code)
    mock_recall_api.get_headers.reset_mock()

    result = recall_adapter.schedule_recall_bot(event_id, meeting_url)
    assert result is None
    mock_post.assert_called_once()
    mock_recall_api.get_headers.assert_called_once()

def test_schedule_recall_bot_no_url(mock_recall_api):
    mock_recall_api.get_headers.reset_mock()
    result = recall_adapter.schedule_recall_bot("evt_no_url", "")
    assert result is None
    # requests.post should not have been called
    mock_recall_api.get_headers.assert_not_called()


# --- Test unschedule_recall_bot ---

@patch('requests.delete')
def test_unschedule_recall_bot_success(mock_delete, mock_recall_api):
    event_id = "evt_unsched_1"
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 204 # Success - No Content
    mock_delete.return_value = mock_response
    # Reset mock before calling function
    mock_recall_api.get_headers.reset_mock()

    success = recall_adapter.unschedule_recall_bot(event_id)

    assert success is True
    mock_delete.assert_called_once_with(
        f"{RECALL_API_BASE_URL}/calendar-events/{event_id}/bot/",
        headers=mock_recall_api.get_headers.return_value # Check against return value
    )
    mock_recall_api.get_headers.assert_called_once() # Verify headers were fetched

@patch('requests.delete')
def test_unschedule_recall_bot_not_found(mock_delete, mock_recall_api):
    event_id = "evt_unsched_404"
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 404 # Not Found
    mock_response.json.return_value = {"detail": "Not found."}
    mock_delete.return_value = mock_response
    # Adjust handler for non-204 status if needed for logging, etc.
    mock_recall_api.handle_response = lambda r: (r.json(), r.status_code)
    mock_recall_api.get_headers.reset_mock()

    success = recall_adapter.unschedule_recall_bot(event_id)
    assert success is True # Treat 404 as success (bot is not scheduled)
    mock_delete.assert_called_once()
    mock_recall_api.get_headers.assert_called_once()

@patch('requests.delete')
def test_unschedule_recall_bot_failure(mock_delete, mock_recall_api):
    event_id = "evt_unsched_fail"
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 500
    mock_response.json.return_value = {"detail": "Server Error"}
    mock_delete.return_value = mock_response
    mock_recall_api.handle_response = lambda r: (r.json(), r.status_code)
    mock_recall_api.get_headers.reset_mock()

    success = recall_adapter.unschedule_recall_bot(event_id)
    assert success is False
    mock_delete.assert_called_once()
    mock_recall_api.get_headers.assert_called_once()

# --- Test check_and_process_finished_bots ---

@pytest.fixture
def setup_finished_bot_test(temp_folders, mock_recall_api, mock_boto3_s3, mock_subprocess, mocker):
    """Sets up mocks and initial data for testing finished bot processing."""
    user_id = "proc_user"
    meeting_id = "proc_mtg_1"
    bot_id = "proc_bot_123"
    user_data = {
        "recall_calendar_id": "cal_proc",
        "bots": {
            meeting_id: {
                "bot_id": bot_id,
                "meeting_url": "https://zoom.us/j/proc",
                "title": "Processing Test",
                "scheduled_at": datetime.now(timezone.utc).isoformat(),
                "audio_processed": False,
                "meeting_removed": False
            }
        }
    }
    data_manager.save_user_data(user_id, user_data)

    # Mock Recall API responses
    finished_bot_details = {
        "meeting_title": "Processing Test",
        "start_time": "2024-01-11T10:00:00Z",
        "end_time": "2024-01-11T11:00:00Z",
        "meeting_participants_names": ["Alice", "Bob"],
        "video_url": "https://recall.ai/video/proc_bot_123.mp4" # Needed by download_video
    }
    mock_recall_api.list_finished_bots.return_value = {bot_id: finished_bot_details}

    # Mock download_video
    mock_download = mocker.patch('recall_adapter.recall_download_video')
    # Simulate download creating the file and returning path + participants
    # Use os.path.join for paths
    downloaded_video_path = os.path.join(TEMP_FOLDER, f"{bot_id}.mp4")
    def download_side_effect(b_id, base_path):
        # base_path is expected to be like .../temp/proc_bot_123 (no extension)
        # download_video should create .../temp/proc_bot_123.mp4
        expected_dl_path = base_path + ".mp4"
        with open(expected_dl_path, 'w') as f: f.write('dummy video') # Create dummy file
        return expected_dl_path, ["Alice", "Bob"]
    mock_download.side_effect = download_side_effect

    # Mock S3 checks (file not found initially)
    mock_boto3_s3.list_objects_v2.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

    # Mock conversion and upload (assuming success)
    mock_popen, mock_proc = mock_subprocess # Unpack from fixture
    mock_proc.returncode = 0
    mock_boto3_s3.upload_file.return_value = None

    # Mock metadata saving
    mocker.patch('utils.save_meeting_metadata', return_value=True)
    # Mock cleanup
    mock_cleanup = mocker.patch('media_processing.cleanup_temp_files')


    # Return the unpacked mock_subprocess tuple
    return user_id, meeting_id, bot_id, mock_recall_api, mock_download, mock_boto3_s3, (mock_popen, mock_proc), mock_cleanup


def test_process_finished_bot_already_in_s3(setup_finished_bot_test):
    user_id, meeting_id, bot_id, _, mock_download, mock_s3, mock_ffmpeg_popen_tuple, mock_cleanup = setup_finished_bot_test
    mock_ffmpeg_popen, mock_ffmpeg_proc = mock_ffmpeg_popen_tuple

    # Simulate files already existing in S3
    s3_audio_key = f"{user_id}/{meeting_id}/recording.mp3"
    s3_meta_key = f"{user_id}/{meeting_id}/metadata.json"

    def s3_list_side_effect(Bucket, Prefix, MaxKeys):
        if Prefix == s3_audio_key:
            return {'Contents': [{'Key': s3_audio_key}], 'ResponseMetadata': {'HTTPStatusCode': 200}}
        elif Prefix == s3_meta_key:
            return {'Contents': [{'Key': s3_meta_key}], 'ResponseMetadata': {'HTTPStatusCode': 200}}
        else:
            return {'ResponseMetadata': {'HTTPStatusCode': 200}}
    mock_s3.list_objects_v2.side_effect = s3_list_side_effect

    user_data = data_manager.load_user_data(user_id)
    processed, removed, modified = recall_adapter.check_and_process_finished_bots(user_id, user_data)

    assert processed == 1
    assert modified is True

    # Should not download, convert, upload, or cleanup
    mock_download.assert_not_called()
    mock_ffmpeg_popen.assert_not_called()
    mock_s3.upload_file.assert_not_called()
    mock_cleanup.assert_not_called()

    # Verify user_data update
    bot_final_data = user_data['bots'][meeting_id]
    assert bot_final_data['audio_processed'] is True
    assert bot_final_data['audio_url'] == f"s3://{S3_BUCKET}/{s3_audio_key}"
    assert bot_final_data['metadata_url'] == f"s3://{S3_BUCKET}/{s3_meta_key}"
    assert 'processed_at' in bot_final_data


@pytest.mark.usefixtures("freezer") # Add fixture marker
def test_check_orphaned_bot_removed(temp_folders, mock_recall_api, freezer): # Add freezer arg
    """Test that an old, removed meeting's bot is removed if Recall says 404."""
    user_id = "orphan_user"
    meeting_id = "orphan_mtg"
    bot_id = "orphan_bot"
    removal_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    # Use BOT_REMOVAL_CHECK_HOURS from config
    freezer.move_to(removal_time + timedelta(hours=BOT_REMOVAL_CHECK_HOURS + 1))

    user_data = {
        "bots": {
            meeting_id: {
                "bot_id": bot_id, "audio_processed": False,
                "meeting_removed": True, "removed_at": removal_time.isoformat()
            }
        }
    }
    data_manager.save_user_data(user_id, user_data)

    # Mock Recall API: list_finished_bots returns empty, check_bot_status returns 404
    mock_recall_api.list_finished_bots.return_value = {}
    mock_recall_api.check_bot_status.return_value = (None, 404)

    # Run the check
    processed, removed, modified = recall_adapter.check_and_process_finished_bots(user_id, user_data)

    assert processed == 0
    assert removed == 1 # Orphaned bot was removed
    assert modified is True

    # Check that the bot entry is gone from user_data
    assert meeting_id not in user_data['bots']
    mock_recall_api.check_bot_status.assert_called_once_with(bot_id)


@pytest.mark.usefixtures("freezer") # Add fixture marker
def test_check_orphaned_bot_kept(temp_folders, mock_recall_api, freezer): # Add freezer arg
    """Test that an old, removed meeting's bot is kept if Recall says it still exists."""
    user_id = "orphan_user_kept"
    meeting_id = "orphan_mtg_kept"
    bot_id = "orphan_bot_kept"
    removal_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    # Use BOT_REMOVAL_CHECK_HOURS from config
    freezer.move_to(removal_time + timedelta(hours=BOT_REMOVAL_CHECK_HOURS + 1))

    user_data = {
        "bots": {
            meeting_id: {
                "bot_id": bot_id, "audio_processed": False,
                "meeting_removed": True, "removed_at": removal_time.isoformat()
            }
        }
    }
    data_manager.save_user_data(user_id, user_data)

    # Mock Recall API: list_finished_bots returns empty, check_bot_status returns 200
    mock_recall_api.list_finished_bots.return_value = {}
    mock_recall_api.check_bot_status.return_value = ({"status": "processing", "video_url": None}, 200)

    processed, removed, modified = recall_adapter.check_and_process_finished_bots(user_id, user_data)

    assert processed == 0
    assert removed == 0 # Bot was kept
    assert modified is False # No change to user data state

    # Bot entry should still exist
    assert meeting_id in user_data['bots']
    mock_recall_api.check_bot_status.assert_called_once_with(bot_id)
