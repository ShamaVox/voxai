from flask import Flask, send_from_directory, request, jsonify
import os
from flask_cors import CORS
from datetime import date, timedelta
import random # temporary
import re

app = Flask(__name__, static_folder='../client/dist')
CORS(app, resources={r"/*": {"origins": ["http://localhost:8081", "http://localhost:5000", "http://localhost:80"]}})

isAccepted = False

first_names = [
    "John", "Emma", "Michael", "Olivia", "William", "Ava", "James", "Sophia", 
    "Benjamin", "Isabella", "Ethan", "Mia", "Noah", "Amelia", "Lucas", "Harper",
    "Mason", "Evelyn", "Logan", "Abigail", "Oliver", "Emily", "Jacob", "Elizabeth",
    "Matthew", "Avery"
]
last_names = [
    "Smith", "Johnson", "Brown", "Taylor", "Miller", "Davis", "Garcia", 
    "Wilson", "Martinez", "Anderson", "Thomas", "Moore", "Martin", "Jackson", 
    "Thompson", "White", "Lopez", "Lee", "Gonzalez", "Harris", "Clark", "Lewis",
    "Robinson", "Walker", "Perez", "Hall"
]
roles = [
    "Software Engineer", "Product Manager", "UX Designer", "Data Analyst", 
    "Marketing Specialist", "Data Scientist", "DevOps Engineer", "QA Tester", 
    "Cloud Architect", "Security Engineer", "Web Developer", "Mobile Developer",
    "Game Developer", "Database Administrator", "System Administrator", 
    "Business Analyst", "Project Manager", "Technical Writer", "UI/UX Designer",
    "Content Creator", "Digital Marketer", "Sales Representative", 
    "Customer Support Specialist"
]
companies = [
    "ABC Inc.", "XYZ Corp.", "Acme Co.", "Delta Ltd.", "Epsilon LLC", 
    "Globex Industries", "Stark Enterprises", "Wayne Tech", "Oscorp", 
    "Umbrella Corporation", "Cyberdyne Systems", "Tyrell Corporation", 
    "Initech", "Massive Dynamic", "Wonka Industries", "Buy n Large", 
    "Hooli", "Acme Corporation", "Soylent Corporation", "Omni Consumer Products",
    "Aperture Science", "Weyland-Yutani Corp", "Blue Sun Corporation"
]

def get_random(max_value, negative=False):
    if not negative:
        return random.randint(0, max_value)
    else:
        return random.randint(-max_value, max_value)

def get_random_item(array):
    return random.choice(array)

def get_random_date():
    start_date = date(2024, 5, 1)
    end_date = date(2024, 11, 30)
    random_delta = timedelta(days=random.randint(0, (end_date - start_date).days))
    return (start_date + random_delta).isoformat()

def get_random_time():
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    return f"{hours:02d}:{minutes:02d}"

def generate_verification_code():
    # Placeholder
    return 123123

def send_verification_code(email, code):
    # Placeholder
    pass 

def is_valid_verification_code(email, code): 
    # Placeholder
    if code == "123123":
        return True 
    return False

def is_valid_email(email):
    # Regular expression pattern for email validation
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_pattern, email) is not None

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
        if is_valid_email(email):
            # Generate and send verification code to the email
            verification_code = generate_verification_code()
            send_verification_code(email, verification_code)
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
        if is_valid_verification_code(email, code):
            data = {
                "message": "Verification code is valid",
            }
            return_code = 200
        else:
            data = {
                "message": "Invalid verification code",
            }
            return_code = 401
        return jsonify(data), return_code

@app.route("/api/insights")
def get_insights():
    lower_compensation = get_random(100)
    insights = {
        "candidateStage": get_random(5),
        "fittingJobApplication": get_random(10),
        "fittingJobApplicationPercentage": get_random(25, negative=True),
        "averageInterviewPace": get_random(7),
        "averageInterviewPacePercentage": get_random(25, negative=True),
        "lowerCompensationRange": lower_compensation,
        "upperCompensationRange": lower_compensation + get_random(100),
    }
    return jsonify(insights)

@app.route("/api/interviews")
def get_interviews():
    interviews = []
    for _ in range(10):
        interviews.append({
            "id": len(interviews) + 1,
            "date": get_random_date(),
            "time": get_random_time(),
            "candidateName": f"{get_random_item(first_names)} {get_random_item(last_names)}",
            "currentCompany": get_random_item(companies),
            "interviewers": f"{get_random_item(first_names)} {get_random_item(last_names)}, {get_random_item(first_names)} {get_random_item(last_names)}",
            "role": get_random_item(roles),
        })
    return jsonify(interviews)

if __name__ == '__main__':
    app.run()
