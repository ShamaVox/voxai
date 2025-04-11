import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timezone, timedelta # Import timedelta

import calendar_processing
import data_manager
import recall_adapter
import oauth
# Get patched path as string, convert back if needed, but mostly passed as string arg
from config import TOKENS_FOLDER as TOKENS_FOLDER_STR, DATA_FOLDER as DATA_FOLDER_STR
from pathlib import Path

TOKENS_FOLDER = Path(TOKENS_FOLDER_STR)
DATA_FOLDER = Path(DATA_FOLDER_STR)


# Sample data
USER_ID = "cal_test_user"
TOKEN_DATA = {
    "token": "google_access", "refresh_token": "google_refresh",
    "client_id": "google_cid", "client_secret": "google_csec",
    "token_uri": "google_uri", "scopes": ["cal_scope"], "expiry": "2099..."
}
RECALL_CALENDAR_ID = "recall_cal_123"

# Simple time strings for easier comparison in mocks if exact datetime isn't needed
MEETING_1_OLD = {"id": "m1", "start_time": "T10", "end_time": "T11", "meeting_url": "url1", "calendar_id": RECALL_CALENDAR_ID}
MEETING_2_OLD = {"id": "m2", "start_time": "T14", "end_time": "T15", "meeting_url": "url2", "calendar_id": RECALL_CALENDAR_ID}
MEETING_1_NEW = {"id": "m1", "start_time": "T10", "end_time": "T11", "meeting_url": "url1_changed", "calendar_id": RECALL_CALENDAR_ID} # Changed URL
MEETING_3_NEW = {"id": "m3", "start_time": "T16", "end_time": "T17", "meeting_url": "url3", "calendar_id": RECALL_CALENDAR_ID} # New meeting


@pytest.fixture
def setup_calendar_test(temp_folders, mocker, mock_recall_api):
    """Common setup for calendar processing tests."""
    # Mock dependencies
    mock_refresh = mocker.patch('calendar_processing.refresh_token_if_needed')
    # Simulate successful refresh returning valid mock credentials
    mock_creds = MagicMock()
    mock_creds.token = "refreshed_google_token"
    mock_creds.refresh_token = "refreshed_google_refresh"
    # Use datetime objects directly for expiry
    mock_creds.expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_refresh.return_value = mock_creds

    # Mock Recall adapter functions (use mock_recall_api where possible)
    mock_list_events = mocker.patch('recall_adapter.list_calendar_events', return_value=[]) # Default: no events
    mock_process_events = mocker.patch('recall_adapter.process_recall_events_for_sync', return_value=[]) # Default: no events
    mock_schedule = mocker.patch('recall_adapter.schedule_recall_bot', return_value={"bot_id": "bot_new_123"}) # Default: success
    mock_unschedule = mocker.patch('recall_adapter.unschedule_recall_bot', return_value=True) # Default: success

    # Save initial token data
    data_manager.save_token_data(USER_ID, TOKEN_DATA)

    return {
        "mock_refresh": mock_refresh,
        "mock_list_events": mock_list_events,
        "mock_process_events": mock_process_events,
        "mock_schedule": mock_schedule,
        "mock_unschedule": mock_unschedule,
        "mock_recall_api": mock_recall_api # From fixture
    }

# --- Test process_user_calendar ---

def test_process_user_calendar_new_user(setup_calendar_test):
    """Test flow for a user with no existing data (needs Recall calendar creation)."""
    mocks = setup_calendar_test
    # mock_recall_api fixture already mocks create_calendar successfully

    # Run processing
    success = calendar_processing.process_user_calendar(USER_ID, TOKEN_DATA)

    assert success is True
    mocks["mock_refresh"].assert_called_once_with(USER_ID)
    # Check if create_calendar was called (via mock_recall_api fixture)
    mocks["mock_recall_api"].create_calendar.assert_called_once()
    mocks["mock_list_events"].assert_called_once_with("cal_12345") # Uses created ID
    mocks["mock_process_events"].assert_called_once() # With empty list from list_events
    mocks["mock_schedule"].assert_not_called() # No events to schedule
    mocks["mock_unschedule"].assert_not_called()

    # Verify user data saved
    user_data = data_manager.load_user_data(USER_ID)
    assert user_data["recall_calendar_id"] == "cal_12345"
    assert user_data["meetings"] == []
    assert user_data["last_updated"] is not None

def test_process_user_calendar_existing_user_no_changes(setup_calendar_test):
    """Test flow for existing user with no meeting changes."""
    mocks = setup_calendar_test
    # Setup existing user data
    initial_user_data = {
        "recall_calendar_id": RECALL_CALENDAR_ID,
        "meetings": [MEETING_1_OLD],
        "bots": {"m1": {"bot_id": "bot_old_1", "audio_processed": False}},
        "last_updated": "some_old_timestamp"
    }
    data_manager.save_user_data(USER_ID, initial_user_data)

    # Mock API to return the same meeting
    mocks["mock_list_events"].return_value = [{"id": "m1_raw"}] # Raw event from Recall
    mocks["mock_process_events"].return_value = [MEETING_1_OLD] # Processed event

    success = calendar_processing.process_user_calendar(USER_ID, TOKEN_DATA)

    assert success is True
    mocks["mock_refresh"].assert_called_once()
    mocks["mock_recall_api"].create_calendar.assert_not_called() # Already exists
    mocks["mock_list_events"].assert_called_once_with(RECALL_CALENDAR_ID)
    mocks["mock_process_events"].assert_called_once()
    mocks["mock_schedule"].assert_not_called()
    mocks["mock_unschedule"].assert_not_called()

    # Verify user data update (only timestamp and potentially meetings list)
    user_data = data_manager.load_user_data(USER_ID)
    assert user_data["recall_calendar_id"] == RECALL_CALENDAR_ID
    assert user_data["meetings"] == [MEETING_1_OLD] # Stored the current list
    assert user_data["bots"] == {"m1": {"bot_id": "bot_old_1", "audio_processed": False}} # Bots unchanged
    assert user_data["last_updated"] != "some_old_timestamp"

def test_process_user_calendar_new_meeting(setup_calendar_test):
    """Test scheduling a bot for a new meeting."""
    mocks = setup_calendar_test
    initial_user_data = {"recall_calendar_id": RECALL_CALENDAR_ID, "meetings": [], "bots": {}}
    data_manager.save_user_data(USER_ID, initial_user_data)

    # Mock API return: one new meeting
    mocks["mock_process_events"].return_value = [MEETING_3_NEW]

    success = calendar_processing.process_user_calendar(USER_ID, TOKEN_DATA)

    assert success is True
    # Verify schedule_recall_bot was called for the new meeting
    mocks["mock_schedule"].assert_called_once_with(MEETING_3_NEW["id"], MEETING_3_NEW["meeting_url"])
    mocks["mock_unschedule"].assert_not_called()

    # Verify bot data was added
    user_data = data_manager.load_user_data(USER_ID)
    assert "m3" in user_data["bots"]
    assert user_data["bots"]["m3"]["bot_id"] == "bot_new_123" # From mock_schedule return
    assert user_data["bots"]["m3"]["meeting_url"] == MEETING_3_NEW["meeting_url"]
    assert user_data["meetings"] == [MEETING_3_NEW]

# Use freezegun fixture for time-sensitive tests
@pytest.mark.usefixtures("freezer")
def test_process_user_calendar_removed_meeting_future(freezer, setup_calendar_test):
    """Test unscheduling a bot for a removed future meeting."""
    mocks = setup_calendar_test
    freezer.move_to('2024-01-01T12:00:00Z') # Assume now is before the meeting

    # Old meeting scheduled in the future relative to frozen time
    future_meeting = {"id": "m_future", "start_time": "2024-01-01T14:00:00Z", "end_time": "2024-01-01T15:00:00Z", "meeting_url": "url_future"}

    initial_user_data = {
        "recall_calendar_id": RECALL_CALENDAR_ID,
        "meetings": [future_meeting],
        "bots": {"m_future": {"bot_id": "bot_future_1", "audio_processed": False}}
    }
    data_manager.save_user_data(USER_ID, initial_user_data)

    # Mock API return: empty list (meeting removed)
    mocks["mock_process_events"].return_value = []

    success = calendar_processing.process_user_calendar(USER_ID, TOKEN_DATA)

    assert success is True
    mocks["mock_schedule"].assert_not_called()
    # Verify unschedule_recall_bot was called for the removed meeting
    mocks["mock_unschedule"].assert_called_once_with(future_meeting["id"])

    # Verify bot data was removed
    user_data = data_manager.load_user_data(USER_ID)
    assert "m_future" not in user_data["bots"]
    assert user_data["meetings"] == []


@patch('calendar_processing.is_meeting_in_past', return_value=True) # Force meeting to be 'past'
def test_process_user_calendar_removed_meeting_past(mock_is_past, setup_calendar_test):
    """Test keeping bot entry for a removed meeting that's in the past."""
    mocks = setup_calendar_test
    # Define meeting with ISO format times for is_meeting_in_past mock compatibility
    past_meeting = {"id": "m_past", "start_time": "2024-01-01T08:00:00Z", "end_time": "2024-01-01T09:00:00Z", "meeting_url": "url_past"}
    initial_user_data = {
        "recall_calendar_id": RECALL_CALENDAR_ID,
        "meetings": [past_meeting],
        "bots": {"m_past": {"bot_id": "bot_past_1", "audio_processed": False}}
    }
    data_manager.save_user_data(USER_ID, initial_user_data)

    # Mock API return: empty list (meeting removed)
    mocks["mock_process_events"].return_value = []

    success = calendar_processing.process_user_calendar(USER_ID, TOKEN_DATA)

    assert success is True
    mock_is_past.assert_called_once_with(past_meeting) # Check helper was called
    mocks["mock_schedule"].assert_not_called()
    mocks["mock_unschedule"].assert_not_called() # Should NOT unschedule

    # Verify bot data was kept but marked as removed
    user_data = data_manager.load_user_data(USER_ID)
    assert "m_past" in user_data["bots"]
    assert user_data["bots"]["m_past"]["bot_id"] == "bot_past_1"
    assert user_data["bots"]["m_past"]["meeting_removed"] is True # Marked for later check
    assert "removed_at" in user_data["bots"]["m_past"]
    assert user_data["meetings"] == []


def test_process_user_calendar_changed_meeting(setup_calendar_test):
    """Test unscheduling old and scheduling new bot for a changed meeting."""
    mocks = setup_calendar_test
    initial_user_data = {
        "recall_calendar_id": RECALL_CALENDAR_ID,
        "meetings": [MEETING_1_OLD],
        "bots": {"m1": {"bot_id": "bot_old_1", "meeting_url": "url1"}}
    }
    data_manager.save_user_data(USER_ID, initial_user_data)

    # Mock API return: Meeting 1 with changed URL
    mocks["mock_process_events"].return_value = [MEETING_1_NEW]

    success = calendar_processing.process_user_calendar(USER_ID, TOKEN_DATA)

    assert success is True
    # Verify unschedule was called for the old bot
    mocks["mock_unschedule"].assert_called_once_with(MEETING_1_OLD["id"])
    # Verify schedule was called with the new URL
    mocks["mock_schedule"].assert_called_once_with(MEETING_1_NEW["id"], MEETING_1_NEW["meeting_url"])

    # Verify bot data was updated
    user_data = data_manager.load_user_data(USER_ID)
    assert "m1" in user_data["bots"]
    assert user_data["bots"]["m1"]["bot_id"] == "bot_new_123" # From mock_schedule
    assert user_data["bots"]["m1"]["meeting_url"] == MEETING_1_NEW["meeting_url"]
    assert user_data["meetings"] == [MEETING_1_NEW]


def test_process_user_calendar_token_refresh_fails(setup_calendar_test):
    """Test that processing stops if token refresh fails."""
    mocks = setup_calendar_test
    # Simulate refresh failure
    mocks["mock_refresh"].return_value = None

    success = calendar_processing.process_user_calendar(USER_ID, TOKEN_DATA)

    assert success is False
    mocks["mock_refresh"].assert_called_once_with(USER_ID)
    # Subsequent steps should not be called
    mocks["mock_recall_api"].create_calendar.assert_not_called()
    mocks["mock_list_events"].assert_not_called()


def test_process_user_calendar_recall_calendar_creation_fails(setup_calendar_test):
    """Test that processing stops if Recall calendar creation fails."""
    mocks = setup_calendar_test
    # Simulate create_calendar failure
    mocks["mock_recall_api"].create_calendar.return_value = ({"detail": "Failed"}, 500)

    # Ensure no initial user data exists
    user_data_path = DATA_FOLDER / f"{USER_ID}_data.json"
    if user_data_path.exists():
        user_data_path.unlink()


    success = calendar_processing.process_user_calendar(USER_ID, TOKEN_DATA)

    assert success is False
    mocks["mock_recall_api"].create_calendar.assert_called_once()
    # Subsequent steps should not be called
    mocks["mock_list_events"].assert_not_called()

# --- Test check_all_calendars ---

@patch('calendar_processing.process_user_calendar', return_value=True)
@patch('recall_adapter.check_and_process_finished_bots', return_value=(0, 0, False)) # Proc count, removed count, modified flag
@patch('data_manager.get_token_files', return_value=["user1.json", "user2.json"])
@patch('data_manager.load_token_data')
@patch('data_manager.load_user_data')
@patch('data_manager.save_user_data')
def test_check_all_calendars_success(mock_save_user, mock_load_user, mock_load_token, mock_get_tokens, mock_check_finished, mock_process_user):
    """Test the main loop processing multiple users."""

    # Mock token loading to return some data
    mock_load_token.side_effect = lambda filename: {"token": filename}
    # Mock user data loading
    mock_load_user.side_effect = lambda user_id: {"bots": {}} if user_id == "user1" else {"bots": {"m1": {"bot_id": "b1"}}}

    calendar_processing.check_all_calendars()

    # Assert process_user_calendar called for each user
    assert mock_process_user.call_count == 2
    mock_process_user.assert_has_calls([
        call("user1", {"token": "user1.json"}),
        call("user2", {"token": "user2.json"})
    ], any_order=True)

    # Assert check_and_process_finished_bots called for each user
    assert mock_check_finished.call_count == 2
    # Check calls based on the mocked user data loaded
    mock_check_finished.assert_has_calls([
        call("user1", {"bots": {}}),
        call("user2", {"bots": {"m1": {"bot_id": "b1"}}})
    ], any_order=True)

    # Assert user data was NOT saved because mock_check_finished returned modified=False
    mock_save_user.assert_not_called()


@patch('calendar_processing.process_user_calendar', side_effect=[True, Exception("User 2 Failed")]) # User 1 succeeds, User 2 fails
@patch('recall_adapter.check_and_process_finished_bots', return_value=(1, 0, True)) # Simulate one processed, data modified
@patch('data_manager.get_token_files', return_value=["user1.json", "user2.json"])
@patch('data_manager.load_token_data')
@patch('data_manager.load_user_data')
@patch('data_manager.save_user_data')
def test_check_all_calendars_user_failure(mock_save_user, mock_load_user, mock_load_token, mock_get_tokens, mock_check_finished, mock_process_user):
    """Test that the loop continues and finished check runs even if one user fails."""

    mock_load_token.side_effect = lambda filename: {"token": filename}
    mock_load_user.return_value = {"bots": {"m1": {}}} # Same data for both for simplicity here

    calendar_processing.check_all_calendars()

    # process_user_calendar was called for both
    assert mock_process_user.call_count == 2

    # check_finished should still be called for both, even though user 2 failed earlier
    assert mock_check_finished.call_count == 2

    # User data should be saved for both because mock_check_finished returned modified=True
    assert mock_save_user.call_count == 2
    mock_save_user.assert_has_calls([
        call("user1", {"bots": {"m1": {}}}), # Data passed to check_finished is saved back
        call("user2", {"bots": {"m1": {}}})
    ], any_order=True)
