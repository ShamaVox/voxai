import base64
from flask import jsonify, request
import io
import json
import os
from pdfminer.high_level import extract_text
import requests
import time
import random
import re

from .auth import sessions

from ..app import app 
from ..database import Account, db, Organization, Role, Skill
from ..input_validation import validate_field_onboarding
from ..utils import handle_auth_token, upload_file

@app.route('/api/onboarding', methods=['POST'])
def onboarding():
    current_user_id = handle_auth_token(sessions)
    if current_user_id is None:
        return valid_token_response(False) 
    try:
        data = request.json

        # Validate all fields
        errors = {}
        for field in ['jobDescriptionFile', 'companyWebsite', 'companySize', 
        'hiringDocument', 'jobTitle', 'positionType', 'department', 'jobSummary', 
        'responsibilities', 'jobRequirements', 'hardSkills', 'softSkills', 
        'behavioralSkills']:
            error = validate_field_onboarding(field, data.get(field))
            if error:
                errors[field] = error

        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        # If validation passes, proceed with data processing
        if 'companyName' in data:
            organization = Organization.query.filter_by(name=data['companyName']).first()
            if not organization:
                # Create a new organization if it doesn't exist
                organization = Organization(name=data['companyName'])
                db.session.add(organization)
        else:
            # If companyName is not provided, get the organization from the account
            account = Account.query.get(account_id)
            organization = account.organization
        
        organization.website_url = data['companyWebsite']
        organization.size = int(data['companySize'])
        
        # Handle hiring document upload
        if data['hiringDocument']:
            hiring_doc = data['hiringDocument'][0]['uri']
            # TODO: use organization.name + "_hiring_document" as name
            # Currently uploading all files to the same location to avoid wasting S3 space
            upload_file("hiring_document", hiring_doc)

        db.session.add(organization)

        # Create Role
        role = Role(
            role_name=data['jobTitle'],
            position_type=data['positionType'],
            department=data['department'],
            responsibilities=data['responsibilities'],
            requirements=data['jobRequirements']
        )

        # Add skills to the role
        for skill_data in data['hardSkills'] + data['softSkills'] + data['behavioralSkills']:
            skill_name = skill_data['skill_name']
            skill = Skill.query.filter_by(skill_name=skill_name).first()
            if not skill:
                skill = Skill(skill_name=skill_name)
                db.session.add(skill)
            role.skills.append(skill)

        db.session.add(role)

        # Update Account (assuming the account already exists and we're updating it)
        account = Account.query.filter_by(account_id=current_user_id).first()
        if account:
            account.organization = organization
            account.onboarded = True
            db.session.add(account)

        db.session.commit()

        return jsonify({"success": True, "message": "Onboarding completed successfully"}), 200

    except NameError as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/sync-google-calendar', methods=['POST'])
def sync_google_calendar():
    current_user_id = handle_auth_token(sessions)
    if current_user_id is None:
        return valid_token_response(False)

    try:
        data = request.json
        access_token = data.get('accessToken')

        if not access_token:
            return jsonify({"success": False, "message": "Access token is required"}), 400

        # Get the current user's account
        account = Account.query.get(current_user_id)
        if not account:
            return jsonify({"success": False, "message": "Account not found"}), 404

        # Update the account with the new access token
        account.google_calendar_token = access_token
        db.session.commit()

        return jsonify({"success": True})

        # TODO: Implement something like this utilizing Google Calendar
        # from google.oauth2.credentials import Credentials
        # from googleapiclient.discovery import build
        # from googleapiclient.errors import HttpError
        # # Use the access token to fetch calendar events
        # creds = Credentials(token=access_token)
        # service = build('calendar', 'v3', credentials=creds)

        # # Call the Calendar API
        # now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        # events_result = service.events().list(calendarId='primary', timeMin=now,
        #                                       maxResults=10, singleEvents=True,
        #                                       orderBy='startTime').execute()
        # events = events_result.get('items', [])

        # if not events:
        #     return jsonify({"success": True, "message": "No upcoming events found"}), 200

        # # Process and store the events as needed
        # # For now, we'll just return the number of events synced
        # return jsonify({
        #     "success": True, 
        #     "message": f"Successfully synced {len(events)} events",
        #     "events_count": len(events)
        # }), 200

    # except HttpError as error:
    #     return jsonify({"success": False, "message": f"An error occurred: {error}"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

def extract_data_from_pdf(pdf_file, skills):
    text = extract_text(pdf_file)
    
    # Simple regex patterns to extract information
    company_name = re.search(r'Company:\s*(.*)', text, re.IGNORECASE)
    job_title = re.search(r'Job Title:\s*(.*)', text, re.IGNORECASE)
    department = re.search(r'Department:\s*(.*)', text, re.IGNORECASE)
    responsibilities = re.findall(r'Responsibilities:(.*?)(?:Requirements|\Z)', text, re.DOTALL | re.IGNORECASE)
    requirements = re.findall(r'Requirements:(.*?)(?:Qualifications|\Z)', text, re.DOTALL | re.IGNORECASE)
    detected_skills = []
    for skill in skills:
        if skill.skill_name.lower() in text.lower():
            skill_type = random.choice(['hard', 'soft', 'behavioral'])
            detected_skills.append({
                "skill_id": skill.skill_id,
                "skill_name": skill.skill_name,
                "type": skill_type
            })

    return {
        'companyName': company_name.group(1) if company_name else '',
        'jobTitle': job_title.group(1) if job_title else '',
        'department': department.group(1) if department else '',
        'responsibilities': [r.strip() for r in responsibilities[0].split('\n') if r.strip()] if responsibilities else [],
        'requirements': [r.strip() for r in requirements[0].split('\n') if r.strip()] if requirements else [],
        'detected_skills': detected_skills,
    }

def allowed_file(filename):
    return filename.split(".")[-1] == "pdf"

@app.route('/api/process-files', methods=['POST'])
def process_files():
    try:
        data = request.json
        extracted_data = {}
        temp_dir = os.path.expanduser("~/Desktop/temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Fetch all skills from the database
        skills = Skill.query.all()

        # Process job description file
        job_description_file = data.get('jobDescriptionFile')
        if job_description_file and job_description_file[0].get('uri'):
            file_content = base64.b64decode(job_description_file[0]['uri'].split(',')[1])
            file_name = f"job_description_{job_description_file[0]['name']}"
            file_path = os.path.join(temp_dir, file_name)
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            with open(file_path, 'rb') as f:
                extracted_data.update(extract_data_from_pdf(f, skills))
            
            os.remove(file_path)  # Remove the file after processing

        # Process hiring document file
        hiring_document = data.get('hiringDocument')
        if hiring_document and hiring_document[0].get('uri'):
            file_content = base64.b64decode(hiring_document[0]['uri'].split(',')[1])
            file_name = f"hiring_document_{hiring_document[0]['name']}"
            file_path = os.path.join(temp_dir, file_name)
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            with open(file_path, 'rb') as f:
                hiring_data = extract_data_from_pdf(f, skills)
                extracted_data = {**hiring_data, **extracted_data}
            
            os.remove(file_path)  # Remove the file after processing

        # Process job description URL
        job_description_url = data.get('jobDescriptionUrl')
        if job_description_url:
            response = requests.get(job_description_url)
            if response.status_code == 200:
                pdf_content = io.BytesIO(response.content)
                extracted_data.update(extract_data_from_pdf(pdf_content, skills))

        # Process hiring document URL
        hiring_document_url = data.get('hiringDocumentUrl')
        if hiring_document_url:
            response = requests.get(hiring_document_url)
            if response.status_code == 200:
                pdf_content = io.BytesIO(response.content)
                hiring_data = extract_data_from_pdf(pdf_content, skills)
                extracted_data = {**hiring_data, **extracted_data}

        if not extracted_data:
            return jsonify({"success": False, "message": "No data could be extracted from the provided files or URLs"}), 400

        # Combine detected skills from all sources
        all_detected_skills = []
        if 'detected_skills' in extracted_data:
            all_detected_skills.extend(extracted_data['detected_skills'])
            del extracted_data['detected_skills']

        # Remove duplicates while preserving order
        seen = set()
        unique_detected_skills = []
        for skill in all_detected_skills:
            if skill['skill_id'] not in seen:
                seen.add(skill['skill_id'])
                unique_detected_skills.append(skill)

        # Add the unique detected skills to the response
        extracted_data['detected_skills'] = unique_detected_skills

        return jsonify({"success": True, "data": extracted_data}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500