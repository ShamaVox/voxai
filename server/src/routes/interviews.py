from flask import jsonify, request
from os import environ

from .auth import sessions

from ..app import app as app
from ..queries import get_account_interviews
from ..synthetic_data import fake_interview
from ..utils import handle_auth_token, valid_token_response

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
