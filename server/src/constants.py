import sys 
import os

# Score required for an application to count for "fitting job application" metric
MATCH_THRESHOLD = 80

# Number of days to average for calculating changes in Insight metrics
METRIC_HISTORY_DAYS_TO_AVERAGE = 7

# Number of days to average when calculating interview pace
INTERVIEW_PACE_DAYS_TO_AVERAGE = 7

# Number of days to average when calculating change in interview pace
INTERVIEW_PACE_CHANGE_DAYS_TO_AVERAGE = 30

# Number of entries for each table when creating an account
SYNTHETIC_DATA_ENTRIES = 3 if 'TEST' in os.environ else 10

# Number of batches during account creation
SYNTHETIC_DATA_BATCHES = 2 if 'TEST' in os.environ else 10 

# Print debug lines for synthetic data
DEBUG_SYNTHETIC_DATA = False 

# Whether to preprocess audio and video during synthetic data generation
ENABLE_SYNTHETIC_PREPROCESSING = "pytest" not in sys.modules and 'TEST' not in os.environ

# Whether to get sentiment for completed interviews during synthetic data generation
ENABLE_SYNTHETIC_SENTIMENT = "pytest" not in sys.modules 

# Whether to get engagement for completed interviews during synthetic data generation
ENABLE_SYNTHETIC_ENGAGEMENT = "pytest" not in sys.modules 

# Percentage of completed interviews to call APIs for during synthetic data generation
SYNTHETIC_INTERVIEW_PROCESSING_PERCENTAGE = 10

# A list of skills to use during data generation
SKILL_LIST = set([
    # Technical Skills
    # Programming Languages
    "Python", "Java", "C++", "JavaScript", "TypeScript", "C#", "PHP", "Go", "Swift", "Kotlin", "R", 
    "Ruby", "Rust", "Scala", 

    # Web Development
    "HTML", "CSS", "React", "Angular", "Vue.js", "Node.js", "Django", "Flask", "ASP.NET", "Ruby on Rails", 

    # Databases
    "SQL", "NoSQL", "MySQL", "PostgreSQL", "MongoDB", "Cassandra", "Redis", "SQLite", 

    # Cloud and DevOps
    "AWS", "Azure", "Google Cloud Platform", "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", 

    # Data Science and Analytics
    "Machine Learning", "Deep Learning", "Data Analysis", "Data Visualization", "Statistics", 
    "Big Data", "Apache Spark", "Hadoop", "Tableau", "Power BI", 

    # Other Technical Skills
    "Git", "GitHub", "Linux", "Unix", "Agile", "Scrum", "Kanban", "Testing", "QA", "UI/UX Design", 

    # General Workplace Skills
    # Communication and Collaboration
    "Communication", "Teamwork", "Collaboration", "Interpersonal skills", "Public speaking", 
    "Presentation skills", "Active listening", "Written communication", "Nonverbal communication",

    # Problem-Solving and Critical Thinking
    "Problem-solving", "Critical thinking", "Analytical thinking", "Decision-making", "Troubleshooting",
    "Logical reasoning", "Creativity", "Innovation", 

    # Organizational and Time Management
    "Time management", "Organization", "Planning", "Prioritization", "Goal setting", "Scheduling", 
    "Multitasking", 

    # Leadership and Management
    "Leadership", "Management", "Delegation", "Motivation", "Coaching", "Mentoring", "Performance management",
    "Conflict resolution", 

    # Adaptability and Learning
    "Adaptability", "Flexibility", "Learning agility", "Continuous learning", "Problem-solving", 
    "Willingness to learn",

    # Other Workplace Skills
    "Customer service", "Negotiation", "Research", "Analysis", "Project management", "Business acumen", 
    "Emotional intelligence", "Stress management", "Work ethic"
])

# Filepaths for third-party API credentials
AWS_CREDENTIAL_FILEPATH = os.path.expanduser("~/.aws/credentials.json")
RECALL_CREDENTIAL_FILEPATH = os.path.expanduser("~/.aws/credentials.json") # TODO: change