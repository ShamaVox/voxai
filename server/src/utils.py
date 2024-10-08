import boto3
from botocore.exceptions import BotoCoreError, ClientError
from datetime import date, timedelta
from flask import jsonify, make_response, request
import json
from os import environ
import random
import requests
import string
from urllib.parse import urlparse

from .constants import RECALL_CREDENTIAL_FILEPATH, AWS_CREDENTIAL_FILEPATH, DEBUG_RECALL_INTELLIGENCE, DEBUG_RECALL_RECORDING_RETRIEVAL

# Configure S3 settings and create an S3 client
S3_BUCKET_NAME = 'voxai-test-audio-video'
aws_credentials = json.load(open(AWS_CREDENTIAL_FILEPATH))
s3_client = boto3.client('s3', aws_access_key_id=aws_credentials['aws_access_key_id'], aws_secret_access_key=aws_credentials['aws_secret_access_key'])

def get_random(max_value, negative=False):
    """Generates a random integer within a specified range."""
    if not negative:
        return random.randint(0, max_value)
    else:
        return random.randint(-max_value, max_value)

def get_random_item(array):
    """Selects a random item from an array."""
    return random.choice(array)

def get_random_date():
    """
    Generates a random date string within a specified range.

    Returns:
        A string representing a random date in ISO format (YYYY-MM-DD).
    """
    start_date = date(2024, 5, 1)
    end_date = date(2024, 11, 30)
    random_delta = timedelta(days=random.randint(0, (end_date - start_date).days))
    return (start_date + random_delta).isoformat()

def get_random_time():
    """
    Generates a random time string in 24-hour format.

    Returns: 
        A string representing a random time in the format HH:MM. 
    """
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    return f"{hours:02d}:{minutes:02d}"

def get_random_string(length):
    """
    Generates a random string of a specified length using uppercase letters and digits.

    Args:
        length: The desired length of the random string.

    Returns:
        A random string of the specified length.
    """
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

def get_recall_api_key():
    """
    Gets the recall.ai API key from the file it is stored in.

    Returns:
        The recall API key (a string).
    """
    try:
        with open(RECALL_CREDENTIAL_FILEPATH) as f:
            credentials = json.load(f)
        recall_api_key = credentials["recall_api_key"]
        return recall_api_key
    except (FileNotFoundError, KeyError):
        return None

def get_recall_headers():
    """
    Returns an object with the headers for the recall.ai API. 

    Args:
        None, currently (may add some if different APIs require different headers).

    Returns:
        A dictionary containing the header data to send in the request to recall.ai. 
    """
    recall_api_key = get_recall_api_key()
    if recall_api_key is None:
        return {"error": "Missing or incorrect Recall API credentials"}
    return {
        'accept': 'application/json',
        'content-type': 'application/json',
        'Authorization': f'Token {recall_api_key}'
    }

def api_error_response(message, status_code):
    return jsonify({"error": message}), status_code

def valid_token_response(valid_token):
    """Returns a response informing the client of whether the auth token is valid."""
    response = make_response(jsonify({"validToken": valid_token}))
    response.delete_cookie('authToken')
    return response, 200 if valid_token else 401

def handle_auth_token(sessions):
    """
    Handles the authentication token and returns the current user's ID.

    This function retrieves the authentication token from the request cookies and determines the current user's ID based on the token. If the environment is set to "Integration" testing, it assigns a default user ID of 0 (temporary workaround for Jest). Otherwise, it retrieves the user ID from the sessions object using the authentication token.

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

# TODO: move to utils
def upload_file(output_key, file_content):
    """Uploads a file to s3."""
    try:
        # Upload to the new location
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=output_key, Body=file_content)
        
        # Return the new S3 URL
        return f's3://{S3_BUCKET_NAME}/{output_key}'
    except (BotoCoreError, ClientError) as e:
        print(f"Error in S3 operation: {str(e)}")
        return None
    except ValueError as e:
        print(str(e))
        return None


def download_and_reupload_file(input_url, output_key):
    """Download a file from input_url (S3 or HTTP) and re-upload it to a new S3 key."""
    try:
        parsed_url = urlparse(input_url)
        
        if parsed_url.scheme in ['http', 'https']:
            # Handle HTTP/HTTPS URL
            response = requests.get(input_url)
            response.raise_for_status()  # Raise an exception for bad status codes
            file_content = response.content
        elif parsed_url.scheme == 's3':
            # Handle S3 URL
            bucket_name = parsed_url.netloc
            input_key = parsed_url.path.lstrip('/')
            file_content = s3_client.get_object(Bucket=bucket_name, Key=input_key)['Body'].read()
        else:
            raise ValueError(f"Unsupported URL scheme: {parsed_url.scheme}")
        
        # Upload to the new location
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=output_key, Body=file_content)
        
        # Return the new S3 URL
        return f's3://{S3_BUCKET_NAME}/{output_key}'
    except (BotoCoreError, ClientError) as e:
        print(f"Error in S3 operation: {str(e)}")
        return None
    except requests.RequestException as e:
        print(f"Error downloading file from URL: {str(e)}")
        return None
    except ValueError as e:
        print(str(e))
        return None