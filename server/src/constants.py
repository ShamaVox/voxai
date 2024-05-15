import sys 
from os import environ

# Score required for an application to count for "fitting job application" metric
MATCH_THRESHOLD = 80

# Number of days to average for calculating changes in Insight metrics
METRIC_HISTORY_DAYS_TO_AVERAGE = 7

# Number of days to average when calculating interview pace
INTERVIEW_PACE_DAYS_TO_AVERAGE = 7

# Number of days to average when calculating change in interview pace
INTERVIEW_PACE_CHANGE_DAYS_TO_AVERAGE = 30

# Number of entries for each table when creating an account
SYNTHETIC_DATA_ENTRIES = 3 if 'TEST' in environ else 10

# Number of batches during account creation
SYNTHETIC_DATA_BATCHES = 2 if 'TEST' in environ else 10 

# Print debug lines for synthetic data
DEBUG_SYNTHETIC_DATA = False 

# Whether to preprocess audio and video during synthetic data generation
ENABLE_SYNTHETIC_PREPROCESSING = "pytest" not in sys.modules and 'TEST' not in environ

# Whether to get sentiment for completed interviews during synthetic data generation
ENABLE_SYNTHETIC_SENTIMENT = "pytest" not in sys.modules 

# Whether to get engagement for completed interviews during synthetic data generation
ENABLE_SYNTHETIC_ENGAGEMENT = "pytest" not in sys.modules 

# Percentage of completed interviews to call APIs for during synthetic data generation
SYNTHETIC_INTERVIEW_PROCESSING_PERCENTAGE = 10