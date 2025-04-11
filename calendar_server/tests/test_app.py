import pytest
import time
from unittest.mock import patch, MagicMock
import json

# Fixtures `app`, `client`, `runner` are provided by conftest.py
# Fixture `temp_folders` ensures config/data paths are temporary

def test_index_route(client):
    """Test the home page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Calendar Recording Service" in response.data
    assert b"Connect Your Google Calendar" in response.data

def test_health_check_route(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'ok'
    assert 'timestamp' in json_data

def test_favicon_route(client, temp_folders):
    """Test the favicon route."""
    # Ensure dummy favicon exists (created by temp_folders/initialize_folders)
    response = client.get('/favicon.ico')
    assert response.status_code == 200
    assert response.mimetype == 'image/vnd.microsoft.icon'

@patch('app.data_manager') # Mock the whole data_manager module used in the route
def test_stats_route(mock_data_manager, client):
    """Test the stats endpoint."""
    # Configure mocks
    mock_data_manager.get_token_files.return_value = ['user1.json', 'user2.json']
    mock_data_manager.load_user_data.side_effect = [
        { # Data for user1
            "recall_calendar_id": "cal1", "meetings": ["m1"], "bots": {"b1": {}},
            "last_updated": "T1"
        },
        { # Data for user2
            "recall_calendar_id": "cal2", "meetings": ["m2", "m3"], "bots": {"b2": {}, "b3": {}},
            "last_updated": "T2"
        }
    ]

    response = client.get('/stats')
    assert response.status_code == 200
    json_data = response.get_json()

    assert json_data['total_users'] == 2
    assert json_data['total_bots_tracked'] == 3 # 1 + 2
    assert len(json_data['user_details']) == 2
    assert json_data['user_details'][0]['user_id'] == 'user1'
    assert json_data['user_details'][0]['bots_tracked'] == 1
    assert json_data['user_details'][1]['user_id'] == 'user2'
    assert json_data['user_details'][1]['bots_tracked'] == 2
    assert 'timestamp' in json_data

@patch('app.check_all_calendars')
def test_trigger_check_route_success(mock_check_all, client):
    """Test the manual trigger endpoint."""
    response = client.get('/check-now')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'ok'
    assert json_data['message'] == 'Manual check cycle completed.'
    mock_check_all.assert_called_once()

@patch('app.check_all_calendars', side_effect=Exception("Check Failed"))
def test_trigger_check_route_error(mock_check_all, client):
    """Test the manual trigger endpoint when the check fails."""
    response = client.get('/check-now')
    assert response.status_code == 500
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert 'Check Failed' in json_data['message']
    mock_check_all.assert_called_once()


# --- Test CLI Commands ---

@patch('app.check_all_calendars')
def test_cli_check_calendars(mock_check_all, runner):
    """Test the 'flask check-calendars' CLI command."""
    result = runner.invoke(args=['check-calendars'])
    print(f"CLI Output:\n{result.output}") # Print output for debugging
    assert result.exit_code == 0
    assert 'Running check_all_calendars via CLI command...' in result.output
    assert 'CLI command finished.' in result.output
    mock_check_all.assert_called_once()

@patch('app.start_scheduler')
@patch('app.stop_scheduler')
@patch('time.sleep', side_effect=KeyboardInterrupt("Simulated Ctrl+C")) # Raise specific exception
def test_cli_run_scheduler(mock_sleep, mock_stop, mock_start, runner):
    """Test the 'flask run-scheduler' CLI command."""
    result = runner.invoke(args=['run-scheduler'], catch_exceptions=False) # Don't let runner catch KeyboardInterrupt

    print(f"CLI Output:\n{result.output}")
    assert 'Starting scheduler via CLI command...' in result.output
    assert 'Scheduler started in background.' in result.output
    # Check for the specific exception message or a generic interrupt message
    assert 'KeyboardInterrupt received' in result.output # Check if custom message prints
    assert 'Stopping scheduler...' in result.output
    mock_start.assert_called_once()
    mock_sleep.assert_called_once() # Called once before interrupt
    mock_stop.assert_called_once()
