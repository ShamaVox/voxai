import os
import json
import requests
from flask import Blueprint, request, redirect, jsonify, url_for, current_app
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

from config import OAUTH_CONFIG, GOOGLE_SCOPES, TOKENS_FOLDER
import data_manager

oauth_bp = Blueprint('oauth', __name__, url_prefix='/auth')

def refresh_token_if_needed(user_id: str) -> Credentials | None:
    """Refresh Google token if expired and update token file. Returns valid Credentials or None."""
    token_file = f"{user_id}.json"
    token_data = data_manager.load_token_data(token_file)

    if not token_data:
        print(f"No token data found for user {user_id}")
        return None

    # Check if essential OAuth config is loaded for token URI, client ID, secret
    if not OAUTH_CONFIG.get('token_uri') or not OAUTH_CONFIG.get('client_id') or not OAUTH_CONFIG.get('client_secret'):
         print("OAuth configuration (token_uri, client_id, client_secret) is missing. Cannot refresh token.")
         return None

    # Ensure the token data has the necessary fields from the *current* config
    # This helps if the client_secret.json was updated after the token was stored
    token_data['token_uri'] = OAUTH_CONFIG['token_uri']
    token_data['client_id'] = OAUTH_CONFIG['client_id']
    token_data['client_secret'] = OAUTH_CONFIG['client_secret']

    required_fields = ['refresh_token', 'token_uri', 'client_id', 'client_secret', 'scopes']
    missing_fields = [field for field in required_fields if field not in token_data or not token_data[field]]

    if missing_fields:
        print(f"Warning: Token file {token_file} is missing required fields for refresh: {', '.join(missing_fields)}")
        print("This token cannot be refreshed automatically. Please re-authenticate.")
        return None

    try:
        creds = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes')
        )

        if creds.valid:
             return creds

        if not creds.refresh_token:
            print(f"No refresh token available for {user_id}. Cannot refresh. Please re-authenticate.")
            # Optionally, delete the token file as it's unusable for automatic refresh
            # try:
            #     os.remove(os.path.join(TOKENS_FOLDER, token_file))
            #     print(f"Removed unusable token file: {token_file}")
            # except OSError as e:
            #     print(f"Error removing token file {token_file}: {e}")
            return None

        print(f"Refreshing token for {user_id}...")
        creds.refresh(Request()) # Google's library handles the refresh request

        # Update token data with refreshed values
        token_data['token'] = creds.token
        if creds.refresh_token: # Refresh token might be updated by Google
            token_data['refresh_token'] = creds.refresh_token
        if creds.expiry:
            # Ensure expiry is stored in a consistent, serializable format (ISO 8601 UTC)
            token_data['expiry'] = creds.expiry.isoformat().replace('+00:00', 'Z')

        # Save updated token data back to the file
        data_manager.save_token_data(user_id, token_data)

        print(f"Token refreshed successfully for {user_id}")
        return creds

    except Exception as e:
        print(f"Error refreshing token for {user_id}: {str(e)}")
        # Handle specific errors like RefreshError which might indicate revoked access
        if "invalid_grant" in str(e).lower():
             print(f"Refresh failed for {user_id} (likely revoked access). Please re-authenticate.")
             # Optionally delete the token file here too
        return None


def get_user_info(credentials: Credentials) -> dict | None:
    """Get user info (email, id) using valid credentials."""
    if not credentials or not credentials.token:
        print("Error: Cannot get user info without valid credentials token.")
        return None
    try:
        # Use the userinfo endpoint which is standard for OpenID Connect
        userinfo_endpoint = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {credentials.token}'}
        response = requests.get(userinfo_endpoint, headers=headers)
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        user_info = response.json()
        # Basic validation: Ensure 'id' or 'email' is present
        if 'id' not in user_info and 'email' not in user_info:
             print(f"Warning: User info received lacks both 'id' and 'email': {user_info}")
             return None # Or handle based on your needs
        return user_info
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user info: {str(e)}")
        # Log specific details if available (e.g., response content for non-200 status)
        if hasattr(e, 'response') and e.response is not None:
             print(f"Response status: {e.response.status_code}, Content: {e.response.text}")
        return None
    except Exception as e:
        print(f"Unexpected error in get_user_info: {str(e)}")
        return None

@oauth_bp.route('/google')
def google_auth():
    """Redirect user to Google OAuth consent page."""
    if not OAUTH_CONFIG.get('client_id') or not OAUTH_CONFIG.get('redirect_uri'):
        return "OAuth configuration missing or invalid (client_id or redirect_uri). Check config.py and client_secret.json.", 500

    # Use Flow for consistency and standard handling
    flow = Flow.from_client_config(
        client_config={"web": OAUTH_CONFIG}, # Pass the relevant part of the config
        scopes=GOOGLE_SCOPES,
        redirect_uri=OAUTH_CONFIG['redirect_uri'] # Crucial: Must match console & callback
    )

    # Generate the authorization URL with necessary parameters
    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Request refresh token
        prompt='consent'        # Ensure refresh token is always sent (important for re-auth)
    )

    # TODO: store the 'state' in the user's session to prevent CSRF
    print(f"Redirecting to Google Auth URL: {authorization_url}")
    return redirect(authorization_url)


@oauth_bp.route('/google/callback')
def google_callback():
    """Handle the OAuth callback from Google."""
    auth_code = request.args.get('code')
    if not auth_code:
        error = request.args.get('error', 'Unknown error')
        error_description = request.args.get('error_description', 'No description provided.')
        print(f"Authorization failed: Error '{error}'. Description: {error_description}")
        return f"Authorization failed: {error}. Please try authenticating again.", 400

    if not OAUTH_CONFIG.get('client_id') or not OAUTH_CONFIG.get('client_secret') or not OAUTH_CONFIG.get('redirect_uri'):
        return "OAuth server configuration error. Check logs.", 500

    try:
        flow = Flow.from_client_config(
            client_config={"web": OAUTH_CONFIG},
            scopes=GOOGLE_SCOPES,
            redirect_uri=OAUTH_CONFIG['redirect_uri'] # Must match the one used in /google route
        )

        # Exchange the authorization code for credentials (access token, refresh token)
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials # Contains access_token, refresh_token, etc.

        if not credentials or not credentials.token:
            return "Failed to obtain credentials from Google.", 500

        # Get user identifier (email is usually preferred and more stable)
        user_info = get_user_info(credentials)
        if not user_info:
            return "Could not retrieve user information after authentication.", 500

        # Use email as the primary user ID, fallback to Google's unique ID if email is missing
        user_id = user_info.get('email')
        if not user_id:
             user_id = user_info.get('id')
             print(f"Using Google ID ({user_id}) as identifier because email was not found.")
             if not user_id:
                  print(f"CRITICAL: Could not get a unique identifier (email or id) from user info: {user_info}")
                  return "Failed to identify the user.", 500

        print(f"User successfully authenticated: {user_id}")

        # Prepare token data for storage in our format
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            # Store expiry as ISO string (UTC 'Z' format)
            'expiry': credentials.expiry.isoformat().replace('+00:00', 'Z') if credentials.expiry else None
        }

        # Save the token data
        data_manager.save_token_data(user_id, token_data)
        print(f"Token data saved for user {user_id}")

        # Trigger initial calendar processing for the new user
        # Import locally to avoid circular dependency at module load time
        try:
            from calendar_processing import process_user_calendar
            print(f"Triggering initial calendar sync for {user_id}...")
            # Pass the newly obtained, validated token data directly
            success = process_user_calendar(user_id, token_data)
            if success:
                 print(f"Initial calendar sync completed for {user_id}.")
            else:
                 print(f"Initial calendar sync failed for {user_id}. See logs for details.")
        except ImportError:
             print("Error: Could not import 'process_user_calendar'. Initial sync skipped.")
        except Exception as e:
            print(f"Error during initial calendar processing for {user_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            # Don't fail the whole auth flow, but log the error

        return "Authentication successful! Your calendar is now being synced. You can close this window."

    except Exception as e:
        print(f"Error during OAuth callback: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"An internal error occurred during authentication: {str(e)}", 500
