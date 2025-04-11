import os
import sys
from flask import Flask, jsonify, request, redirect, send_from_directory, render_template_string
from datetime import datetime, timezone
import traceback
import time

# --- Configuration and Initialization ---
# Ensure the project root is in the path if running app.py directly
# or using a runner like Gunicorn from the project root.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
     sys.path.insert(0, project_root)
# Ensure the 'hex' directory parent is discoverable if RecallAPI is there
hex_parent = os.path.dirname(project_root)
if hex_parent not in sys.path:
     sys.path.insert(0, hex_parent)


# Import configuration and utility functions
import config
import data_manager
from calendar_processing import check_all_calendars # For manual trigger
from scheduler import start_scheduler, stop_scheduler # Import scheduler functions

# Initialize folders on startup
config.initialize_folders()

# --- Create Flask App ---
app = Flask(__name__, static_folder=config.STATIC_FOLDER)
# Optional: Configure secret key for session management if needed later
# app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_default_dev_secret_key')

# --- Register Blueprints ---
# OAuth routes are now in oauth.py
from oauth import oauth_bp
app.register_blueprint(oauth_bp) # Prefix '/auth' is defined in the blueprint

# --- Basic Routes ---
@app.route('/')
def index():
    """Main page with instructions and link to authenticate."""
    # Simple HTML page
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Calendar Recording Service</title>
        <link rel="icon" href="{{ url_for('static', filename='favicon.ico') }}">
        <style>
            body { font-family: sans-serif; line-height: 1.6; padding: 2em; }
            a { color: #007bff; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .container { max-width: 600px; margin: auto; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Calendar Recording Service</h1>
            <p>This service automatically monitors your Google Calendar and uses Recall.ai to record scheduled meetings.</p>
            <p><a href="{{ url_for('oauth.google_auth') }}">Connect Your Google Calendar</a></p>
            <hr>
            <p><small>Check <a href="{{ url_for('health_check') }}">health</a> or <a href="{{ url_for('stats') }}">stats</a>.</small></p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/health')
def health_check():
    """Basic health check endpoint."""
    # Could add checks here (e.g., database connectivity, Recall API ping)
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@app.route('/stats')
def stats():
    """Provide basic statistics about users and processing."""
    try:
        token_files = data_manager.get_token_files()
        users_stats = []
        total_bots = 0
        total_meetings_synced = 0

        for token_file in token_files:
            user_id = os.path.splitext(token_file)[0]
            user_data = data_manager.load_user_data(user_id)
            bot_count = len(user_data.get('bots', {}))
            meeting_count = len(user_data.get('meetings', []))
            users_stats.append({
                'user_id': user_id, # Be mindful of privacy if exposing emails
                'recall_calendar_id': user_data.get('recall_calendar_id', 'Not Set'),
                'meetings_synced': meeting_count,
                'bots_tracked': bot_count,
                'last_synced_at': user_data.get('last_updated')
            })
            total_bots += bot_count
            total_meetings_synced += meeting_count # This is count from last sync, not historical total

        return jsonify({
            'service_status': 'running', # Assuming if the endpoint is hit, it's running
            'total_users': len(users_stats),
            'total_bots_tracked': total_bots,
            # 'total_meetings_synced_last_run': total_meetings_synced, # Clarify metric
            'user_details': users_stats, # Be careful with sensitive info
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        print(f"Error generating stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- Manual Trigger Route ---
@app.route('/check-now')
def trigger_check():
    """Manually trigger the check_all_calendars function."""
    print("Manual check triggered via /check-now endpoint.")
    try:
        # Run the check synchronously for the request
        # Consider running in background thread for long tasks to avoid request timeout
        check_all_calendars()
        return jsonify({
            'status': 'ok',
            'message': 'Manual check cycle completed.',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        print(f"Error during manually triggered check: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f"Error during manual check: {str(e)}"
        }), 500

# --- Error Handling ---
@app.errorhandler(Exception)
def handle_exception(e):
    """Log and return JSON for unhandled exceptions."""
    # Log the error and stack trace
    tb_str = traceback.format_exc()
    print(f"Unhandled Exception: {e}\n{tb_str}")

    # Get request context if available
    req_info = "No request context"
    if request:
        req_info = {
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "data": request.get_data(as_text=True)
        }
        # Redact sensitive headers like Authorization, Cookie
        if 'Authorization' in req_info['headers']: req_info['headers']['Authorization'] = "REDACTED"
        if 'Cookie' in req_info['headers']: req_info['headers']['Cookie'] = "REDACTED"

    print(f"Request Info: {req_info}")

    # Return a JSON error response
    response = jsonify({
        "error": "Internal Server Error",
        "message": str(e) # In production, might want to hide detailed errors
    })
    response.status_code = 500
    return response

# --- Favicon Route ---
# Moved to config.initialize_folders to create a dummy one if needed
# Flask automatically serves from the 'static' folder if configured.
# The route below ensures it works even if static serving needs help.
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, # Use configured static folder
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


# --- Flask CLI Commands ---
@app.cli.command('check-calendars')
def check_calendars_command():
    """CLI command: Run the calendar check process once."""
    print("Running check_all_calendars via CLI command...")
    check_all_calendars()
    print("CLI command finished.")

@app.cli.command('run-scheduler')
def run_scheduler_command():
    """CLI command: Start the background scheduler."""
    print("Starting scheduler via CLI command...")
    start_scheduler()
    print("Scheduler started in background. Press Ctrl+C to exit Flask CLI.")
    # Keep the command running until interrupted
    try:
        while True:
            time.sleep(3600) # Sleep for a long time, scheduler runs in background
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Stopping scheduler...")
        stop_scheduler()
        print("Exiting CLI command.")


# --- Main Execution Guard ---
if __name__ == "__main__":
    # This block is typically used for development server (`python app.py`)
    # For production, use a WSGI server like Gunicorn or uWSGI.

    print("Starting Flask development server...")
    # Start the background scheduler when running directly
    print("Starting background scheduler...")
    start_scheduler()

    # Run the Flask development server
    # Listen on all interfaces (0.0.0.0) to be accessible externally if needed
    # Use port 8080 as mentioned in OAuth config, or from env var
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True) # Set debug=False for production

    # Cleanup scheduler on exit (though daemon threads might exit abruptly)
    print("Flask server shutting down. Stopping scheduler...")
    stop_scheduler()
    print("Exiting.")
