from bs4 import BeautifulSoup
from flask import jsonify, request
import json
import requests

from ..app import app, api_bp
from ..database import db, Role
from ..sessions import sessions
from ..utils import api_error_response, valid_token_response, handle_auth_token

@api_bp.route('/greenhouse', methods=['POST'])
def parse_greenhouse_jobs():
    """Parses a Greenhouse jobs page and returns a list of job titles."""
    current_user_id = handle_auth_token(sessions)
    if current_user_id is None:
        return valid_token_response(False) 
    url = request.json.get('url')
    if not url:
        return api_error_response("Missing 'url' parameter", 400)

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        job_elements = soup.find_all('a', {'data-mapped': 'true'})

        job_data = []
        for job_element in job_elements:
            if "create your own" in job_element.text.lower():
                continue
            job_title = job_element.text
            job_url = job_element['href']  # Extract the individual job page URL
            job_data.append({"title": job_title, "url": job_url})

            # Add the role to the database
            # TODO: Get the user's ID from the session or authentication mechanism
            new_role = Role(role_name=job_title, direct_manager_id=current_user_id)
            db.session.add(new_role)

            # TODO: Call parse_greenhouse_job(job_url) to parse the individual job page.
                # We can potentially extract data from text like "The salary range for this role is $180,000 - $250,000." An LLM call can potentially extract more data. 
            # parse_greenhouse_job(job_url)

        db.session.commit()  # Commit the changes to the database

        return jsonify({"job_data": job_data}), 200

    except requests.RequestException as e:
        return api_error_response(f"Error fetching Greenhouse page: {str(e)}", 500)

app.register_blueprint(api_bp)