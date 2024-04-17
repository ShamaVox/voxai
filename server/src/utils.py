import random
from datetime import date, timedelta

def get_random(max_value, negative=False):
    if not negative:
        return random.randint(0, max_value)
    else:
        return random.randint(-max_value, max_value)

def get_random_item(array):
    return random.choice(array)

def get_random_date():
    start_date = date(2024, 5, 1)
    end_date = date(2024, 11, 30)
    random_delta = timedelta(days=random.randint(0, (end_date - start_date).days))
    return (start_date + random_delta).isoformat()

def get_random_time():
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    return f"{hours:02d}:{minutes:02d}"