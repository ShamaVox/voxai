from flask import jsonify, make_response, request
import json
from os import environ

from ..app import app as app
from ..database import Account, db, Organization
from ..input_validation import is_valid_email
from ..sessions import sessions
from ..synthetic_data import generate_synthetic_data_on_account_creation
from ..utils import get_random_string, valid_token_response

def generate_verification_code():
    """Generates a placeholder verification code (currently always 123123)."""
    return 123123

def send_verification_code(email, code):
    """Placeholder function for sending a verification code via email."""
    pass 

def is_valid_verification_code(email, code): 
    """Validates a verification code (currently only checks for a specific value)."""
    return code == "123123"

def handle_auth_token(sessions):
    """
    Handles the authentication token and returns the current user's ID.

    This function retrieves the authentication token from the request cookies and determines
    the current user's ID based on the token. If the environment is set to "Integration" testing,
    it assigns a default user ID of 0 (temporary workaround for Jest). Otherwise, it retrieves
    the user ID from the sessions object using the authentication token.

    Args:
        sessions (dict): A dictionary mapping authentication tokens to user IDs.

    Returns:
        int: The current user's ID.

    Notes:
        - This function requires that the authentication token is stored in the 'authToken' cookie.
        - If the environment is set to "Integration" testing (using the 'TEST' environment variable),
          a default user ID of 0 is returned as a temporary workaround for Jest.
        - If the authentication token is invalid or not found in the sessions object, the function
          should handle the case appropriately (e.g., send a logout response).
    """
    auth_token = request.cookies.get('authToken', None)
    if 'TEST' in environ and environ['TEST'] == "Integration":
        # Temporary Jest workaround
        current_user_id = 0
    else:
        if auth_token not in sessions: 
            # Session is invalid, tell user to log out
            return None 
        current_user_id = sessions[auth_token]

    return current_user_id


@app.route('/api/send_code', methods=['POST'])
def send_code():
    """Handles requests to send a verification code to a user's email. 

    Returns:
        A JSON response with a message and a flag indicating if the account exists.
    """
    email = request.json.get('email')
    if is_valid_email(email):
        # Generate and send verification code to the email
        verification_code = generate_verification_code()
        send_verification_code(email, verification_code)
        data = {
            "message": "Verification code sent successfully",
            "account_exists": Account.query.filter_by(email=email).first() is not None
        }
        return_code = 200
    else:
        data = {
            "message": "Invalid email",
        }
        return_code = 400
    
    response = make_response(jsonify(data), return_code)
    response.delete_cookie('authToken')
    return jsonify(data), return_code

@app.route('/api/validate_code', methods=['POST'])
def validate_code():
    """Validates a verification code and handles account creation or login.

    Returns:
        A JSON response with a message, user data, and an authentication token.
    """ 
    email = request.json.get('email')
    code = request.json.get('code')

    # Check code is valid 
    if not is_valid_verification_code(email, code):
        data = {
                "message": "Invalid verification code",
            }
        return_code = 401
    
    else: 
        # Check if email exists in the table
        existing_account = Account.query.filter_by(email=email).first()

        if existing_account:
            # Email exists, fetch name and account type
            auth_token = get_random_string(36)
            sessions[auth_token] = existing_account.account_id

            data = {
                "message": "Verification code is valid",
                "name": existing_account.name,
                "account_type": existing_account.account_type,
                "email": email,
                "authToken": auth_token,
                "onboarded": existing_account.onboarded,
                "okta": False,
            }
            return_code = 200
            
        else:
            # Email doesn't exist, create a new entry

            # TODO: Move this to input_validation.py and run stronger validation
            if not request.json.get('name'):
                data = {
                    "message": "A name is needed to create an account"
                }
                return_code = 401
            elif not request.json.get('organization'):
                data = {
                    "message": "An organization is needed to create an account"
                }
                return_code = 401
            elif not request.json.get('accountType'):
                data = {
                    "message": "An account type is needed to create an account"
                }
                return_code = 401
            else: 
                new_account = Account(email=email, name=request.json.get('name'), account_type=request.json.get('accountType'))
                organization = Organization(name=request.json.get('organization'))
                # TODO: reject requests where organization already exists
                db.session.add(organization)
                new_account.organization = organization
                db.session.add(new_account)
                db.session.flush()

                generate_synthetic_data_on_account_creation(new_account.account_id)
                db.session.commit()

                auth_token = get_random_string(36)
                sessions[auth_token] = new_account.account_id
                
                data = {
                    "message": "Account created",
                    "name": request.json.get('name'),
                    "organization": request.json.get('organization'),
                    "account_type": request.json.get('accountType'),
                    "email": email,
                    "authToken": auth_token,
                    "onboarded": False,
                    "okta": False,
                }
                return_code = 201 

    response = make_response(jsonify(data), return_code)
    if "authToken" in data:
        response.set_cookie("authToken", value=auth_token, httponly=True, samesite="Strict")
    return response

@app.route('/api/logout', methods=['POST'])
def logout():
    """Handles user logout by removing the authentication token from the session."""
    authToken = request.json.get('authToken')
    if authToken in sessions: 
        del sessions[authToken]
    response = make_response()
    response.delete_cookie('authToken')
    return response

@app.route('/api/check_token', methods=['POST'])
def check_token():
    """Checks if a provided authentication token is valid.""" 

    valid_token = request.json.get('authToken') in sessions or ('TEST' in environ and environ['TEST'] == 'Integration' and request.json.get('authToken') == 'AUTHTOKEN')
    return valid_token_response(valid_token)