import pytest
import time
import threading
from unittest.mock import patch, MagicMock
import schedule # Import schedule

# Assuming scheduler.py is in the root directory or path is set correctly
import scheduler
from config import CHECK_INTERVAL

@patch('scheduler.check_all_calendars', side_effect=Exception("Test Error"))
def test_run_check_all_calendars_job_error_handling(mock_check_all):
    """Test that the job wrapper catches and logs exceptions."""
    # No need to mock schedule here, just call the wrapper directly
    scheduler.run_check_all_calendars_job()
    # Check that the underlying function was called
    mock_check_all.assert_called_once()
    # No crash, implies exception was caught (can also check logs if logger is used)


@patch('threading.Thread')
def test_start_scheduler(mock_thread_class):
    """Test starting the scheduler thread."""
    mock_thread_instance = MagicMock()
    mock_thread_class.return_value = mock_thread_instance

    # Ensure thread is initially None or not alive
    scheduler.scheduler_thread = None
    scheduler.start_scheduler()

    mock_thread_class.assert_called_once_with(target=scheduler.run_scheduler_loop, daemon=True)
    mock_thread_instance.start.assert_called_once()
    assert scheduler.scheduler_running is True
    assert scheduler.scheduler_thread is mock_thread_instance

    # Test starting again when already running
    mock_thread_instance.is_alive.return_value = True
    mock_thread_class.reset_mock()
    mock_thread_instance.start.reset_mock()

    scheduler.start_scheduler()
    mock_thread_class.assert_not_called()
    mock_thread_instance.start.assert_not_called()


def test_stop_scheduler():
    """Test stopping the scheduler thread."""
    mock_thread = MagicMock(spec=threading.Thread)
    mock_thread.is_alive.return_value = True
    scheduler.scheduler_thread = mock_thread
    scheduler.scheduler_running = True

    scheduler.stop_scheduler()

    assert scheduler.scheduler_running is False
    mock_thread.join.assert_called_once_with(timeout=5)


def test_stop_scheduler_not_running():
    """Test stopping when the scheduler is not running."""
    scheduler.scheduler_thread = None
    scheduler.scheduler_running = False
    # Should not raise any error
    scheduler.stop_scheduler()
    assert scheduler.scheduler_running is False
