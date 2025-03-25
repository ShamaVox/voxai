import os
import sys
import json
import time
import datetime
import argparse
import webbrowser
import socket 
import random
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Define the scopes needed for Google Calendar and user info
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 
          'https://www.googleapis.com/auth/userinfo.email',
          'openid']
CLIENT_SECRET_FILE = 'client_secret.json' # Ask for this file 
TOKENS_DIR = 'tokens'

def ensure_tokens_dir():
    """Create the tokens directory if it doesn't exist."""
    if not os.path.exists(TOKENS_DIR):
        os.makedirs(TOKENS_DIR)
        print(f"Created tokens directory: {TOKENS_DIR}")

def get_user_info(credentials):
    """Get user info to identify the account."""
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        return user_info
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None

def credentials_to_dict(credentials):
    """Convert credentials to a dictionary for storage."""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
        'expiry': credentials.expiry.isoformat() if credentials.expiry else None
    }

def print_token_info(credentials, user_info=None):
    """Print information about the token expiration."""
    user_id = user_info.get('email', 'Unknown') if user_info else 'Unknown'
    
    if credentials.expiry:
        now = datetime.datetime.now(datetime.timezone.utc)
        expiry = credentials.expiry.replace(tzinfo=datetime.timezone.utc)
        remaining = expiry - now
        
        print(f"\n--- Token Information for {user_id} ---")
        print(f"Access token expires on: {expiry}")
        print(f"Time until expiration: {remaining.days} days, {remaining.seconds // 3600} hours")
        
        if credentials.refresh_token:
            print("Refresh token is available. The app can automatically refresh the access token.")
        else:
            print("WARNING: No refresh token available. The user will need to reauthorize.")

def run_auth_server_multiple(repeat_count=1, auto_open_browser=True, ngrok_url=None):
    """
    Run an authorization server that handles multiple users with the same URL.
    
    Args:
        repeat_count: Number of authorizations to process
        auto_open_browser: Whether to open the browser automatically for the first user
        
    Returns:
        list: List of successfully authorized user IDs
    """
    ensure_tokens_dir()
    
    # Use a fixed port for all authorizations
    PORT = 8080
    
    # Create a flow to generate the authorization URL
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE, ' '.join(SCOPES))
    if ngrok_url:
        flow.redirect_uri = ngrok_url
    else:
        flow.redirect_uri = f"http://localhost:{PORT}"
    
    # Generate the authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    
    # Print the authorization URL
    print("\n" + "="*80)
    print("🔐 AUTHORIZATION LINK")
    print("="*80)
    print(f"\n{auth_url}\n")
    print("="*80)
    print("Share this link with users who need to authorize the application.")
    print(f"The server will process {repeat_count} authorizations and then exit.")
    print("="*80 + "\n")
    
    # Open the browser if requested
    if auto_open_browser:
        import webbrowser
        print("Opening browser with authorization link...")
        webbrowser.open(auth_url)
    
    # Create a WSGI application that handles OAuth callbacks
    successful_users = []
    auth_count = 0
    auth_error = None
    
    def auth_app(environ, start_response):
        nonlocal auth_count, auth_error
        
        # Check if this is an OAuth callback
        path = environ.get('PATH_INFO', '')
        query_string = environ.get('QUERY_STRING', '')
        
        # Success page HTML
        success_html = """
        <html>
          <head><title>Authentication Success</title></head>
          <body>
            <h1>Authentication Successful!</h1>
            <p>You have successfully authenticated. You can close this window now.</p>
          </body>
        </html>
        """
        
        # Error page HTML
        error_html = """
        <html>
          <head><title>Authentication Error</title></head>
          <body>
            <h1>Authentication Error</h1>
            <p>An error occurred during authentication. Please try again.</p>
            <p>{}</p>
          </body>
        </html>
        """
        
        # Check if this is a callback request
        if 'code=' in query_string:
            try:
                # Parse the query string
                from urllib.parse import parse_qs
                query_params = parse_qs(query_string)
                
                if 'code' in query_params:
                    # Get the authorization code
                    code = query_params['code'][0]
                    
                    # Create a new flow for this exchange
                    user_flow = InstalledAppFlow.from_client_secrets_file(
                        CLIENT_SECRET_FILE, SCOPES)
                    if ngrok_url:
                        user_flow.redirect_uri = ngrok_url
                    else:
                        user_flow.redirect_uri = f"http://localhost:{PORT}"
                    
                    # Exchange the code for credentials
                    user_flow.fetch_token(code=code)
                    credentials = user_flow.credentials
                    
                    # Get user information
                    user_info = get_user_info(credentials)
                    
                    if user_info and 'email' in user_info:
                        user_id = user_info['email']
                        
                        # Save the credentials
                        token_path = os.path.join(TOKENS_DIR, f"{user_id}.json")
                        with open(token_path, 'w') as f:
                            json.dump(credentials_to_dict(credentials), f)
                        
                        print(f"\n✅ Authorization successful for user: {user_id}")
                        print_token_info(credentials, user_info)
                        
                        # Add to our list of successful users
                        successful_users.append(user_id)
                        
                        # Increment the auth count
                        auth_count += 1
                        
                        # Return success page
                        start_response('200 OK', [('Content-type', 'text/html')])
                        return [success_html.encode('utf-8')]
                    else:
                        auth_error = "Could not identify user from credentials"
                        start_response('400 Bad Request', [('Content-type', 'text/html')])
                        return [error_html.format(auth_error).encode('utf-8')]
                else:
                    auth_error = "No authorization code received"
                    start_response('400 Bad Request', [('Content-type', 'text/html')])
                    return [error_html.format(auth_error).encode('utf-8')]
            except Exception as e:
                import traceback
                auth_error = str(e)
                traceback.print_exc()
                start_response('500 Internal Server Error', [('Content-type', 'text/html')])
                return [error_html.format(auth_error).encode('utf-8')]
        else:
            # Not a callback request
            start_response('404 Not Found', [('Content-type', 'text/plain')])
            return [b'Not Found']
    
    # Set up the WSGI server
    import wsgiref.simple_server
    httpd = wsgiref.simple_server.make_server('localhost', PORT, auth_app)
    
    # Set a reasonable timeout for waiting between requests
    httpd.timeout = 30  # 30 seconds
    
    # Disable request logging
    httpd.RequestHandlerClass.log_message = lambda *args, **kwargs: None
    
    print(f"Server running at http://localhost:{PORT}")
    print(f"Waiting for {repeat_count} authorization(s)...")
    
    try:
        # Run the server until we've processed the requested number of authorizations
        while auth_count < repeat_count:
            httpd.handle_request()
            
            # Skip timeouts and continue waiting
            if auth_count < repeat_count:
                remaining = repeat_count - auth_count
                print(f"Waiting for {remaining} more authorization(s)...")
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    finally:
        httpd.server_close()
    
    return successful_users

def list_users():
    """List all users with tokens and their status."""
    ensure_tokens_dir()
    users = []
    
    for filename in os.listdir(TOKENS_DIR):
        if filename.endswith('.json'):
            user_id = filename[:-5]  # Remove .json extension
            
            # Load the token file
            token_path = os.path.join(TOKENS_DIR, filename)
            with open(token_path, 'r') as f:
                token_data = json.load(f)
            
            # Check expiration
            status = "Unknown"
            if 'expiry' in token_data:
                try:
                    expiry = datetime.datetime.fromisoformat(token_data['expiry'].replace('Z', '+00:00'))
                    now = datetime.datetime.now(datetime.timezone.utc)
                    remaining = expiry - now
                    
                    if now > expiry:
                        status = "Expired"
                    else:
                        status = f"Valid ({remaining.days}d {remaining.seconds//3600}h remaining)"
                except Exception as e:
                    status = f"Invalid expiry format: {e}"
            
            users.append((user_id, status))
    
    if users:
        print("\nAuthorized users:")
        for user_id, status in sorted(users):
            print(f"  {user_id}: {status}")
    else:
        print("\nNo authorized users found.")

def test_token(user_id):
    """Test if a token is valid by making a simple API call."""
    token_path = os.path.join(TOKENS_DIR, f"{user_id}.json")
    
    if not os.path.exists(token_path):
        print(f"No token found for user: {user_id}")
        return False
    
    try:
        # Load the credentials
        with open(token_path, 'r') as f:
            creds_data = json.load(f)
            credentials = Credentials.from_authorized_user_info(creds_data, SCOPES)
        
        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            
            # Save refreshed credentials
            with open(token_path, 'w') as f:
                json.dump(credentials_to_dict(credentials), f)
        
        # Make a test API call
        service = build('calendar', 'v3', credentials=credentials)
        calendars = service.calendarList().list(maxResults=10).execute()
        
        print(f"✅ Token for {user_id} is valid")
        print(f"Found {len(calendars.get('items', []))} calendars")
        
        return True
    except Exception as e:
        print(f"❌ Token for {user_id} is invalid: {e}")
        return False

def main():
    """Main function to process arguments and execute the script."""
    parser = argparse.ArgumentParser(description='Google Calendar API Authorization Tool')
    
    parser.add_argument('--list-users', action='store_true', help='List all users with tokens')
    parser.add_argument('--test', type=str, metavar='EMAIL', help='Test a specific user\'s token')
    parser.add_argument('--repeat', type=int, default=1, help='Number of authorizations to process')
    parser.add_argument('--browser', action='store_true', help='Open browser automatically', default=False)
    parser.add_argument('--ngrok_url', type=str, help='Ngrok URL to use as redirect_uri', default=None)
    
    args = parser.parse_args()
    
    if args.list_users:
        list_users()
        return
    
    if args.test:
        test_token(args.test)
        return
    
    # Process authorizations
    auto_open_browser = args.browser
    repeat_count = max(1, args.repeat)
    ngrok_url = args.ngrok_url
    
    # Run the auth server to process multiple authorizations with the same URL
    successful_users = run_auth_server_multiple(
        repeat_count=repeat_count,
        auto_open_browser=auto_open_browser,
        ngrok_url=ngrok_url
    )
    
    # Show summary
    if successful_users:
        print(f"\n🎉 Successfully authorized {len(successful_users)} users:")
        for user in successful_users:
            print(f"  - {user}")
    else:
        print("\nNo users were successfully authorized.")

if __name__ == "__main__":
    main()