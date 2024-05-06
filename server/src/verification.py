def generate_verification_code():
    """Generates a placeholder verification code (currently always 123123)."""
    return 123123

def send_verification_code(email, code):
    """Placeholder function for sending a verification code via email."""
    pass 

def is_valid_verification_code(email, code): 
    """Validates a verification code (currently only checks for a specific value)."""
    return code == "123123"