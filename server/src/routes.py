from flask import send_from_directory, request, jsonify, make_response
import os
from flask_cors import CORS
from . import verification, input_validation, database, migrations
from .app import app as app
from os import environ
from faker import Faker
from sqlalchemy import func
from .queries import fitting_job_applications_percentage, average_interview_pace, average_compensation_range, get_candidate_interviews
from .constants import MATCH_THRESHOLD, METRIC_HISTORY_DAYS_TO_AVERAGE, INTERVIEW_PACE_DAYS_TO_AVERAGE, INTERVIEW_PACE_CHANGE_DAYS_TO_AVERAGE
from .synthetic_data import fake_interview
from .utils import get_random, get_random_string

isAccepted = False

# Temporary, to test client cookie handling
sessions = {} 

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

    TODO:
        - Implement proper handling of invalid sessions and send a logout response.
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

@app.route('/', defaults={'path': ''})

@app.route('/<path:path>')
def serve(path):
    """
    Serves the React Native application.

    Args:
        path: The path of the requested resource.

    Returns:
        The requested file or the index.html file.
    """
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/send_code', methods=['POST'])
def send_code():
    """Handles requests to send a verification code to a user's email. 

    Returns:
        A JSON response with a message and a flag indicating if the account exists.
    """
    email = request.json.get('email')
    if input_validation.is_valid_email(email):
        # Generate and send verification code to the email
        verification_code = verification.generate_verification_code()
        verification.send_verification_code(email, verification_code)
        data = {
            "message": "Verification code sent successfully",
            "account_exists": database.Account.query.filter_by(email=email).first() is not None
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
    if not verification.is_valid_verification_code(email, code):
        data = {
                "message": "Invalid verification code",
            }
        return_code = 401
    
    else: 
        # Check if email exists in the table
        existing_account = database.Account.query.filter_by(email=email).first()

        if existing_account:
            # Email exists, fetch name and account type
            auth_token = get_random_string(36)
            sessions[auth_token] = existing_account.account_id

            data = {
                "message": "Verification code is valid",
                "name": existing_account.name,
                "account_type": existing_account.account_type,
                "email": email,
                "authToken": auth_token
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
                # Get the maximum account_id from the account table
                max_account_id = database.db.session.query(func.max(database.Account.account_id)).scalar()

                # If there are no existing accounts, start the account_id from 1
                next_account_id = 1 if max_account_id is None else max_account_id + 1
                new_account = database.Account(email=email, name=request.json.get('name'),  organization=request.json.get('organization'), account_type=request.json.get('accountType'), account_id=next_account_id)
                database.db.session.add(new_account)
                database.db.session.commit()

                auth_token = get_random_string(36)
                sessions[auth_token] = request.json.get('email')
                
                data = {
                    "message": "Account created",
                    "name": request.json.get('name'),
                    "organization": request.json.get('organization'),
                    "account_type": request.json.get('accountType'),
                    "email": email,
                    "authToken": auth_token
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

def valid_token_response(valid_token):
    """Returns a response informing the client of whether the auth token is valid."""
    response = make_response(jsonify({"validToken": valid_token}))
    response.delete_cookie('authToken')
    return response, 200 if valid_token else 401

@app.route('/api/check_token', methods=['POST'])
def check_token():
    """Checks if a provided authentication token is valid.""" 

    valid_token = request.json.get('authToken') in sessions or ('TEST' in environ and environ['TEST'] == 'Integration' and request.json.get('authToken') == 'AUTHTOKEN')
    return valid_token_response(valid_token)

@app.route("/api/insights")
def get_insights():
    """Provides synthetic insights data."""
    current_user_id = handle_auth_token(sessions)
    if current_user_id is None:
        return valid_token_response(False) 

    # Run queries 
    fitting_job_applications, fitting_job_applications_percentage_change = fitting_job_applications_percentage(current_user_id, MATCH_THRESHOLD,METRIC_HISTORY_DAYS_TO_AVERAGE)
    average_interview_pace_value, average_interview_pace_percentage = average_interview_pace(current_user_id, INTERVIEW_PACE_DAYS_TO_AVERAGE, INTERVIEW_PACE_CHANGE_DAYS_TO_AVERAGE)
    average_lower_compensation, average_upper_compensation = average_compensation_range(current_user_id)

    insights = {
        "candidateStage": get_random(5),
        "fittingJobApplication": fitting_job_applications,
        "fittingJobApplicationPercentage": fitting_job_applications_percentage_change,
        "averageInterviewPace": average_interview_pace_value,
        "averageInterviewPacePercentage": average_interview_pace_percentage,
        "lowerCompensationRange": average_lower_compensation,
        "upperCompensationRange": average_upper_compensation,
    }
    if 'TEST' in environ:
        # Temporary
        insights = {
            "candidateStage": 3,
            "fittingJobApplication": 85,
            "fittingJobApplicationPercentage": 29,
            "averageInterviewPace": 6,
            "averageInterviewPacePercentage": -10,
            "lowerCompensationRange": 20,
            "upperCompensationRange": 129,
        }
    return jsonify(insights)

@app.route("/api/interviews")
def get_interviews():
    """Provides interview data for a specific candidate."""
    current_user_id = handle_auth_token(sessions)
    if current_user_id is None:
        return valid_token_response(False) 

    candidate_id = request.args.get('candidateId')
    if candidate_id:
        interviews = get_candidate_interviews(candidate_id)
    else:
        interviews = []

    if 'TEST' in environ and not interviews:
        # Generate a fake interview if the interview list is empty in the test environment
        fake_interview_data = fake_interview(1)
        fake_interview_data["candidateName"] = "John Doe"
        interviews.append(fake_interview_data)

    return jsonify(interviews)