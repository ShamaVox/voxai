import random
from datetime import date, timedelta
import string
import json
from flask import jsonify, make_response, request
from .constants import RECALL_CREDENTIAL_FILEPATH
from os import environ

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