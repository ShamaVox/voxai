import json
import sys
import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

"""
This is a test script to validate Google Calendar API calls to get meetings.

Needs to be reworked to be part of the server (such that meetings are checked every so often and Recall is configured to join them). 
"""

def main():
    # Check if token file is provided as a command-line argument
    if len(sys.argv) < 2:
        print("Usage: python script.py <token_file.json>")
        sys.exit(1)
    
    token_file = sys.argv[1]
    
    # Load token data from JSON file
    try:
        with open(token_file, 'r') as f:
            token_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Token file '{token_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in token file '{token_file}'.")
        sys.exit(1)
    
    # Create credentials from token data
    try:
        creds = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes')
        )
    except Exception as e:
        print(f"Error creating credentials: {e}")
        sys.exit(1)
    
    # Check if token is expired and refresh if needed
    try:
        # If the token has expired, refresh it
        if not creds.valid:
            print("Token is expired or invalid, refreshing...")
            creds.refresh(Request())
            
            # Update token data with refreshed values
            token_data['token'] = creds.token
            if creds.refresh_token:  # Only update if we received a new refresh token
                token_data['refresh_token'] = creds.refresh_token
            if creds.expiry:
                token_data['expiry'] = creds.expiry.isoformat().replace('+00:00', 'Z')
            
            # Save updated token data back to the original file
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            print("Token refreshed and saved.")
    except Exception as e:
        print(f"Error during token refresh: {e}")
        sys.exit(1)
    
    # Build the Google Calendar API service
    try:
        service = build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error building Calendar API service: {e}")
        sys.exit(1)
    
    # Call the Calendar API to retrieve upcoming events
    try:
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print("Getting upcoming calendar events...")
        
        # Get events for the next 30 days
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=(datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
    except Exception as e:
        print(f"Error retrieving events: {e}")
        sys.exit(1)
    
    # Process events and extract relevant information
    meetings = []
    
    if not events:
        print("No upcoming events found.")
    else:
        for event in events:
            meeting_info = {
                'summary': event.get('summary', 'No Title'),
                'id': event.get('id'),
                'start': event.get('start', {}),
                'end': event.get('end', {}),
                'location': event.get('location', ''),
                'htmlLink': event.get('htmlLink', ''),
                'hangoutLink': event.get('hangoutLink', '')
            }
            meetings.append(meeting_info)
        
        print(f"Found {len(meetings)} events.")
    
    # Save meetings info to a new JSON file
    # For now, just save in tokens directory 
    output_file = os.path.splitext(token_file)[0] + '_meetings.json'
    try:
        with open(output_file, 'w') as f:
            json.dump({
                'meetings': meetings,
                'retrieved_at': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"Meeting information saved to {output_file}")
    except Exception as e:
        print(f"Error saving meeting information: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()