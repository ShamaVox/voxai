import re

def is_valid_email(email):
    """Validates an email address using a regular expression."""
    return re.match(r'^[\w\.\+-]+@[\w\.-]+\.\w+$', email) is not None