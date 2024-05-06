import random
from datetime import date, timedelta
import string

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