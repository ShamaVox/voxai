from flask import jsonify, redirect, render_template_string, request
import json
import os
import requests
from threading import Lock
import time


from .auth import sessions

from ..app import app 
from ..constants import DEBUG_OKTA
from ..database import Account, db
from ..synthetic_data import generate_synthetic_data_on_account_creation
from ..utils import get_random_string

isAccepted = False

# For paused requests
pending_requests = {}
pending_requests_lock = Lock()

# Okta configuration
# TODO: Set this information in environment variables (client id is set in the front end as well)
OKTA_CLIENT_ID = '0oaitt4y79BThLYvY5d7'
OKTA_CLIENT_SECRET = '6Mw9w_N7FIYvvsntXy1shnSKHexnEBZMNyiGqC9XF53Hzq6win2cIdKBGamxG_cm'
OKTA_ISSUER = 'https://dev-05459793.okta.com/oauth2'
OKTA_REDIRECT_URI = 'http://localhost:5000/okta'

# TODO: Refactor account creation via okta to use a shared function with regular account creation and remove repeated code

@app.route('/okta')
def process_okta():
    code = request.args.get('code')
    state = request.args.get('state')
    if not code:
        return jsonify({"error": "No code provided"}), 400
    if state not in pending_requests:
        return jsonify({"error": "Login timed out"}), 408
    try:
        # Exchange code for tokens
        token_url = f"{OKTA_ISSUER}/default/v1/token"
        token_payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': OKTA_REDIRECT_URI,
            'client_id': OKTA_CLIENT_ID,
            'client_secret': OKTA_CLIENT_SECRET
        }
        token_response = requests.post(token_url, data=token_payload)
        tokens = token_response.json()

        if "access_token" not in tokens:
            return jsonify({"error": "Error during token exchange"}), 500

        # Get user info
        userinfo_url = f"{OKTA_ISSUER}/default/v1/userinfo"
        userinfo_headers = {'Authorization': f"Bearer {tokens['access_token']}"}
        userinfo_response = requests.get(userinfo_url, headers=userinfo_headers)
        userinfo = userinfo_response.json()

        email = userinfo.get('email')

        if not email:
            return jsonify({"error": "Unable to get user email"}), 500

        # Check if the user exists in the database
        existing_account = Account.query.filter_by(email=email).first()

        if existing_account:
            # User exists, log them in
            auth_token = get_random_string(36)
            sessions[auth_token] = existing_account.account_id
            name = existing_account.name 
            onboarded = existing_account.onboarded
            
        else:
            # User doesn't exist, create a new account
            new_account = Account(
                email=email,
                name=userinfo.get('name', 'Default Name').replace("  ", " "),
                account_type='Recruiter' 
            )
            db.session.add(new_account)
            db.session.flush()

            generate_synthetic_data_on_account_creation(new_account.account_id)
            db.session.commit()

            auth_token = get_random_string(36)
            sessions[auth_token] = new_account.account_id
            name = new_account.name
            onboarded = False
        
        with pending_requests_lock:
            if state in pending_requests:
                pending_requests[state]['email'] = email 
                pending_requests[state]['name'] = name
                pending_requests[state]['authToken'] = auth_token
                pending_requests[state]['onboarded'] = onboarded

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login complete</title>
        </head>
        <body>
            Login complete. You can close this tab.
            <script>
                window.close();
            </script>
        </body>
        </html>
        """
        return render_template_string(html)

    except requests.exceptions.RequestException as e:
        if not DEBUG_OKTA:
            app.logger.error(f"Error during Okta communication: {str(e)}")
            return jsonify({"error": "Error during Okta authentication"}), 500
        else:
            raise

@app.route('/api/okta', methods=['POST'])
def okta_login():
    state = request.json['state']
    
    with pending_requests_lock:
        pending_requests[state] = {'timestamp': time.time()}
    
    # Wait for up to 30 seconds for API2 to respond
    start_time = time.time()
    while time.time() - start_time < 300:
        with pending_requests_lock:
            if 'authToken' in pending_requests.get(state, {}):
                auth_token = pending_requests[state]['authToken']
                email = pending_requests[state]['email']
                onboarded = pending_requests[state]['onboarded']
                name = pending_requests[state]['name']
                del pending_requests[state]

                # Process the code and log the user in
                response = jsonify({
                    "success": True,
                    "email": email,
                    "name": name,
                    "authToken": auth_token,
                    "okta": True
                })
                response.set_cookie("authToken", value=auth_token, httponly=True, samesite="Strict")
                return response
        time.sleep(0.5)
    
    # If we've waited too long, remove the pending request and return an error
    with pending_requests_lock:
        if state in pending_requests:
            del pending_requests[state]
    return jsonify({'success': False, 'message': 'Login timeout'}), 408
