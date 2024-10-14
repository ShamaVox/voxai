from flask import jsonify, make_response, request
import json

from .auth import sessions

from ..app import app 
from ..database import db, Interview
from ..utils import handle_auth_token, valid_token_response

@app.route("/api/set_recall_id", methods=["POST"])
def set_interview_recall_id():
    """Sets the recall id value for an interview to allow the analysis result to be queried."""
    current_user_id = handle_auth_token(sessions)
    if current_user_id is None:
        return valid_token_response(False) 

    recall_id = request.json.get('recall_id')
    interview = Interview.query.filter_by(interview_id=request.json.get('id')).first()
    interview.recall_id = recall_id 
    db.session.commit()
    return make_response(jsonify({"success": True})), 200
