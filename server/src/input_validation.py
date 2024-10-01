import re

def is_valid_email(email):
    """Validates an email address using a regular expression."""
    return re.match(r'^[\w\.\+-]+@[\w\.-]+\.\w+$', email) is not None

def validate_field_onboarding(field, value):
    if field in ['jobDescriptionFile', 'hiringDocument']:
        url_field = f"{field}Url"
        return None if value or data.get(url_field) else f"{field} or URL is required"
    elif field in ['jobDescriptionUrl', 'hiringDocumentUrl']:
        if not value:
            return None  # URL is optional if file is provided
        if not re.match(r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$', value):
            return "Invalid URL"
    elif field == 'companyWebsite':
        if not value:
            return "Company website is required"
        if not re.match(r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$', value):
            return "Invalid website URL"
    elif field == 'companySize':
        if not value:
            return "Company size is required"
        try:
            int(value)
        except ValueError:
            return "Company size must be a number"
    elif field in ['jobTitle', 'positionType', 'department', 'jobSummary', 'responsibilities', 'jobRequirements']:
        return None if value else f"{' '.join(re.findall('[A-Z][^A-Z]*', field)).capitalize()} is required"
    elif field in ['hardSkills', 'softSkills', 'behavioralSkills']:
        return None if value and len(value) > 0 else f"At least one {' '.join(re.findall('[A-Z][^A-Z]*', field)).lower()} is required"
    return None
