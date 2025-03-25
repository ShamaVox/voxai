This folder contains a script to obtain Calendar API tokens and a Flask server that will have the bot try to join all meetings in a user's calendar.

# Setup

Run the following in the command line with calendar_server as your local directory:

    python3 -m venv calendar_venv
    source calendar_venv/bin/activate
    pip install -r requirements.txt

# Calendar API Script

Right now, we don't have a persistent server running, so this script is a temporary workaround to get calendar API tokens via mirroring a localhost server with ngrok. There's no way to run the script without updating Google OAuth settings. Once we have a persistent server, it should be possible to run the script from the server without doing this, or build the script functionality directly into the server.

# Flask Server

Not implemented yet, all functions are placeholders.
