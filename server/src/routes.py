from flask import send_from_directory, request, jsonify
import os
from flask_cors import CORS
from . import utils, verification, synthetic_data, input_validation, database
from .app import app as app
from os import environ

isAccepted = False

# Temporary, to test client cookie handling
sessions = {} 

# Serve React Native app
@app.route('/', defaults={'path': ''})

@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/send_code', methods=['POST'])
def send_code():
    if request.method == 'POST':
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
        return jsonify(data), return_code

@app.route('/api/validate_code', methods=['POST'])
def validate_code():
    if request.method == 'POST':
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
                auth_token = utils.get_random_string(36)
                sessions[auth_token] = request.json.get('email')

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
                    database.db.session.commit()

                    auth_token = utils.get_random_string(36)
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

        return jsonify(data), return_code

@app.route("/api/insights")
def get_insights():
    lower_compensation = utils.get_random(100)
    insights = {
        "candidateStage": utils.get_random(5),
        "fittingJobApplication": utils.get_random(10),
        "fittingJobApplicationPercentage": utils.get_random(25, negative=True),
        "averageInterviewPace": utils.get_random(7),
        "averageInterviewPacePercentage": utils.get_random(25, negative=True),
        "lowerCompensationRange": lower_compensation,
        "upperCompensationRange": lower_compensation + utils.get_random(100),
    }
    if 'TEST' in environ:
        # Temporary until there is a table in the database which can be configured for integration testing
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
    interviews = []
    for _ in range(10):
        interviews.append({
            "id": len(interviews) + 1,
            "date": utils.get_random_date(),
            "time": utils.get_random_time(),
            "candidateName": f"{utils.get_random_item(synthetic_data.first_names)} {utils.get_random_item(synthetic_data.last_names)}",
            "currentCompany": utils.get_random_item(synthetic_data.companies),
            "interviewers": f"{utils.get_random_item(synthetic_data.first_names)} {utils.get_random_item(synthetic_data.last_names)}, {utils.get_random_item(synthetic_data.first_names)} {utils.get_random_item(synthetic_data.last_names)}",
            "role": utils.get_random_item(synthetic_data.roles),
        })
    if 'TEST' in environ:
        # Temporary until there is a table in the database which can be configured for integration testing
        interviews[0]["candidateName"] = "John Doe"
    return jsonify(interviews)