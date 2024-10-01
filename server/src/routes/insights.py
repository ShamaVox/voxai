from flask import jsonify
from os import environ

from .auth import sessions

from ..app import app as app
from ..queries import fitting_job_applications_percentage, average_interview_pace, average_compensation_range
from ..utils import get_random, handle_auth_token, valid_token_response

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
