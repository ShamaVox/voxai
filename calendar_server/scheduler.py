import time
import schedule
import threading
from datetime import datetime, timezone

from config import CHECK_INTERVAL
from calendar_processing import check_all_calendars

# Flag to control the scheduler loop
scheduler_running = True
scheduler_thread = None

def run_check_all_calendars_job():
    """Wrapper function to run the main task and handle potential errors."""
    try:
        print(f"\n[{datetime.now(timezone.utc).isoformat()}] Scheduler triggered: Running check_all_calendars...")
        check_all_calendars()
        print(f"[{datetime.now(timezone.utc).isoformat()}] Scheduler job finished.")
    except Exception as e:
        print(f"!!!!!!!!!!!!!! ERROR in scheduled job !!!!!!!!!!!!!!")
        print(f"Error during check_all_calendars: {e}")
        import traceback
        traceback.print_exc()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

def run_scheduler_loop():
    """The main loop for the scheduler thread."""
    global scheduler_running
    print("Scheduler loop started.")

    # Schedule the job
    # Use seconds directly from config for interval
    schedule.every(CHECK_INTERVAL).seconds.do(run_check_all_calendars_job)

    print(f"Scheduled 'check_all_calendars' to run every {CHECK_INTERVAL} seconds.")

    # Run the job once immediately at startup
    print("Running initial check immediately...")
    run_check_all_calendars_job()
    print("Initial check finished.")

    while scheduler_running:
        schedule.run_pending()
        # Sleep for a short duration to avoid busy-waiting
        # Check more frequently than the job interval to ensure timely execution
        sleep_duration = min(60, CHECK_INTERVAL // 10) # Sleep for 1/10th interval or 60s max
        time.sleep(sleep_duration)

    print("Scheduler loop exiting.")

def start_scheduler():
    """Starts the scheduler in a background thread."""
    global scheduler_thread, scheduler_running
    if scheduler_thread is None or not scheduler_thread.is_alive():
        scheduler_running = True
        scheduler_thread = threading.Thread(target=run_scheduler_loop, daemon=True)
        scheduler_thread.start()
        print("Scheduler thread started.")
    else:
        print("Scheduler thread is already running.")

def stop_scheduler():
    """Signals the scheduler thread to stop."""
    global scheduler_running
    if scheduler_thread and scheduler_thread.is_alive():
        print("Stopping scheduler thread...")
        scheduler_running = False
        # Wait briefly for the thread to exit gracefully
        scheduler_thread.join(timeout=5)
        if scheduler_thread.is_alive():
             print("Warning: Scheduler thread did not exit gracefully after 5 seconds.")
        else:
             print("Scheduler thread stopped.")
    else:
        print("Scheduler thread is not running.")

# Support file being executed directly (for testing)
if __name__ == "__main__":
    print("Starting scheduler directly for testing...")
    # Initialize folders needed by the check function
    from config import initialize_folders
    initialize_folders()

    start_scheduler()
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Stopping scheduler...")
        stop_scheduler()
        print("Exiting main thread.")
