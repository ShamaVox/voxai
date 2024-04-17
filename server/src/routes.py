from flask import send_from_directory, request, jsonify
import os
from flask_cors import CORS
from . import utils, verification, synthetic_data, input_validation, database
from .app import app as app

isAccepted = False

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
        # Temporary: Account type is assigned based on verification code
        new_account_type = verification.is_valid_verification_code(email, code)

        if new_account_type is None: 
            data = {
                    "message": "Invalid verification code",
                }
            return_code = 401
        
        else: 
            # Check if email exists in the table
            existing_account = database.Account.query.filter_by(email=email).first()

            if existing_account:
                # Email exists, fetch name and account type
                data = {
                    "message": "Verification code is valid",
                    "name": existing_account.name,
                    "account_type": existing_account.account_type,
                    "email": email
                }
                return_code = 200
                
            else:
                # Email doesn't exist, create a new entry
                name = email.split("@")[0]

                new_account = database.Account(email=email, name=name, account_type=new_account_type)
                database.db.session.add(new_account)
                database.db.session.commit()

                data = {
                    "message": "Account created",
                    "name": name,
                    "account_type": new_account_type,
                    "email": email
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
    return jsonify(interviews)