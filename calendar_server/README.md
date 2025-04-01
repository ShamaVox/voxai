# Calendar Server

A server that connects to Google Calendar, monitors for meetings, schedules Recall.ai recording bots for video calls, and downloads the recordings.

## Overview

This server:

- Authenticates users via Google OAuth
- Monitors their Google Calendar for upcoming meetings
- Automatically schedules Recall.ai bots to join and record meetings
- Processes recordings (converts video to audio)
- Stores recordings in S3 along with meeting metadata

## Setup

### Prerequisites

- Python 3.8+
- ffmpeg (for audio conversion)
- Google OAuth credentials (client_secrets.json)
- Recall.ai API key
- S3 bucket (optional, for storage)

### Installation

1. Clone the repository:

   git clone
   cd calendar-server

2. Install required packages:

   pip install -r requirements.txt

3. Set up Google OAuth:

- Place the `client_secret.json` and `credentials.json` files in the root directory

## Running the Server

There are several ways to run the Calendar Server:

### 1. Flask Development Server

    export FLASK_APP=app.py
    flask run --host=0.0.0.0 --port=8080

### 2. Flask CLI Commands

Check calendars once:

    flask check-calendars

Run the continuous scheduler in the foreground:

    flask run-scheduler

### 3. Standalone Mode

Run the server as a standalone script (includes scheduler):

    python app.py

## API Endpoints

### Authentication

- **GET /auth/google**: Initiates Google OAuth flow
- **GET /auth/google/callback**: Handles OAuth callback

### Status and Management

- **GET /**: Homepage with link to connect calendar
- **GET /health**: Health check endpoint
- **GET /stats**: Server statistics (users, meetings, etc.)
- **GET /check-now**: Manually trigger calendar check
- **GET /check-finished**: Manually check for finished recordings

## Calendar Check Cycle

The server performs these operations periodically:

1. Checks all user tokens in the `tokens` folder
2. Refreshes expired tokens
3. Fetches upcoming calendar events
4. Schedules bots for new meetings
5. Handles rescheduled meetings
6. Checks for finished recordings
7. Processes recordings and uploads to S3

## Configuration

Configuration options are at the top of `app.py`:

- **CHECK_INTERVAL**: Time between calendar checks (default: 3600s/1hour)
- **TOKENS_FOLDER**: Where token files are stored
- **DATA_FOLDER**: Where user data is stored
- **TEMP_FOLDER**: Where temporary files are stored
