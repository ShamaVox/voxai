def generate_verification_code():
    # Placeholder
    return 123123

def send_verification_code(email, code):
    # Placeholder
    pass 

def is_valid_verification_code(email, code): 
    # Placeholder
    # For now, code determines account type 
    if code == "123123":
        return "Recruiter"
    elif code == "321321":
        return "Hiring Manager"
    return None 