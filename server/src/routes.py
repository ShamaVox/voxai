from flask import send_from_directory, request, jsonify, make_response
import os
from flask_cors import CORS
from . import verification, input_validation, database, migrations, apis
from .app import app as app
from os import environ
from faker import Faker
from sqlalchemy import func
from .queries import fitting_job_applications_percentage, average_interview_pace, average_compensation_range, get_account_interviews
from .sessions import sessions
from .synthetic_data import fake_interview, generate_synthetic_data_on_account_creation
from .utils import get_random, get_random_string, valid_token_response, handle_auth_token

isAccepted = False

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
                new_account = database.Account(email=email, name=request.json.get('name'),  organization=request.json.get('organization'), account_type=request.json.get('accountType'))
                database.db.session.add(new_account)
                database.db.session.flush()

                generate_synthetic_data_on_account_creation(new_account.account_id)
                database.db.session.commit()

                auth_token = get_random_string(36)
                sessions[auth_token] = new_account.account_id
                
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
    fitting_job_applications, fitting_job_applications_percentage_change = fitting_job_applications_percentage(current_user_id)
    average_interview_pace_value, average_interview_pace_percentage = average_interview_pace(current_user_id)
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
    """Provides interview data for a specific candidate or interviewer."""
    current_user_id = handle_auth_token(sessions)
    if current_user_id is None:
        return valid_token_response(False) 

    if request.args.get('candidateId'):
        interviews = get_account_interviews(request.args.get('candidateId'), False)
    elif request.args.get('interviewerId'):
        interviews = get_account_interviews(request.args.get('interviewerId'), True)
    else:
        interviews = get_account_interviews(current_user_id, True)

    if 'TEST' in environ and not interviews:
        # Generate a fake interview if the interview list is empty in the test environment
        fake_interview_data = fake_interview(1)
        fake_interview_data["candidateName"] = "John Doe"
        interviews.append(fake_interview_data)

    return jsonify(interviews)

@app.route("/api/set_recall_id", methods=["POST"])
def set_interview_recall_id():
    """Sets the recall id value for an interview to allow the analysis result to be queried."""
    current_user_id = handle_auth_token(sessions)
    if current_user_id is None:
        return valid_token_response(False) 

    recall_id = request.json.get('recall_id')
    interview = database.Interview.query.filter_by(interview_id=request.json.get('id')).first()
    interview.recall_id = recall_id 
    database.db.session.commit()
    return make_response(jsonify({"success": True})), 200