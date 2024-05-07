from faker import Faker
from .database import Account, Role, Application, Candidate, Interview, Skill, MetricHistory, db, interview_skill_score_table, interview_interviewer_speaking_table
from .utils import get_random_time, get_random_date
from .queries import fitting_job_applications_percentage
from os import environ
from .app import app as app
from sqlalchemy import inspect, or_, func
from .constants import SYNTHETIC_DATA_ENTRIES, SYNTHETIC_DATA_BATCHES, DEBUG_SYNTHETIC_DATA
from datetime import datetime, timedelta

data_generator = Faker()

def generate_account_data(num):
    """Generates synthetic data for the Account model.

    Args:
        num_records (int): The number of account records to generate.

    Returns:
        list: A list of generated Account objects.
    """
    account_types = ["Recruiter", "Hiring Manager"]

    accounts = []
    emails = set()
    #for existing_account in Account.query.all():
        #emails.add(existing_account.email)
    for _ in range(num):
        while True:
            # Ensure unique email
            email = data_generator.email()
            email = email.split("@")[0] + "_" + data_generator.name() + "_" + data_generator.company() + email.split("@")[1]
            if email not in emails:
                emails.add(email)
                break  
        name = data_generator.name()
        account_type = data_generator.random_element(account_types)
        organization = data_generator.company()

        account = Account(
            email=email,
            name=name,
            account_type=account_type,
            organization=organization
        )
        accounts.append(account)

    db.session.add_all(accounts)
    db.session.flush()
    return accounts

def generate_role_data(num_records, accounts, skills, direct_manager=None):
    """Generates synthetic data for the Role model.

    Args:
        num_records (int): The number of role records to generate.
        accounts (list): A list of Account objects to be used as direct managers and teammates.
        skills (list): A list of Skill objects to be assigned to the roles.

    Returns:
        list: A list of generated Role objects.
    """
    experience_levels = [1, 2, 3, 4, 5]

    roles = []
    for _ in range(num_records):
        role_name = data_generator.job()
        base_compensation_min = data_generator.random_int(min=50000, max=100000)
        base_compensation_max = data_generator.random_int(min=base_compensation_min, max=150000)
        target_compensation = data_generator.random_int(min=base_compensation_min, max=base_compensation_max)
        experience_level = data_generator.random_element(experience_levels)
        years_of_experience_min = data_generator.random_int(min=0, max=5)
        years_of_experience_max = data_generator.random_int(min=years_of_experience_min, max=10)
        target_years_of_experience = data_generator.random_int(min=years_of_experience_min, max=years_of_experience_max)
        direct_manager = data_generator.random_element(accounts) if direct_manager is None else direct_manager

        role = Role(
            role_name=role_name,
            base_compensation_min=base_compensation_min,
            base_compensation_max=base_compensation_max,
            target_compensation=target_compensation,
            experience_level=experience_level,
            years_of_experience_min=years_of_experience_min,
            years_of_experience_max=years_of_experience_max,
            target_years_of_experience=target_years_of_experience,
            direct_manager=direct_manager
        )

        # Assign random skills to the role
        num_skills = data_generator.random_int(min=1, max=5)
        role_skills = data_generator.random_elements(skills, length=num_skills, unique=True)
        role.skills.extend(role_skills)

        # Assign random teammates to the role
        num_teammates = data_generator.random_int(min=1, max=5)
        role_teammates = data_generator.random_elements(accounts, length=num_teammates, unique=True)
        role.teammates.extend(role_teammates)

        roles.append(role)

    db.session.add_all(roles)
    db.session.flush()
    return roles

def generate_candidate_data(num_records):
    """Generates synthetic data for the Candidate model.

    Args:
        num_records (int): The number of candidate records to generate.

    Returns:
        list: A list of generated Candidate objects.
    """
    interview_stages = [1, 2, 3, 4, 5]

    candidates = []
    for _ in range(num_records):
        candidate_name = data_generator.name()
        current_company = data_generator.company()
        interview_stage = data_generator.random_element(interview_stages)
        resume_url = data_generator.url()

        candidate = Candidate(
            candidate_name=candidate_name,
            current_company=current_company,
            interview_stage=interview_stage,
            resume_url=resume_url
        )
        candidates.append(candidate)

    db.session.add_all(candidates)
    db.session.flush()
    return candidates

def generate_application_data(num_records, roles, candidates):
    """Generates synthetic data for the Application model.

    Args:
        num_records (int): The number of application records to generate.
        roles (list): A list of Role objects to be used as the roles for the applications.
        candidates (list): A list of Account objects representing the candidates who submitted the applications.

    Returns:
        list: A list of generated Application objects.
    """

    applications = []
    pairs = set()
    db.session.flush()
    for _ in range(num_records):
        role = data_generator.random_element(roles)
        candidate = data_generator.random_element(candidates)
        candidate_match = data_generator.random_int(min=0, max=100)
        application_time = data_generator.date_time_between(start_date='-1y', end_date='now')

        for _ in range(100):
            # Check for duplicates
            if (role.role_id, candidate.candidate_id) not in pairs and db.session.query(Application).filter_by(role=role, candidate=candidate).first() is None:
                break
            role = data_generator.random_element(roles)
            candidate = data_generator.random_element(candidates)
        else:
            print("Could not create new Applications: no unique role / candidate pairs")
            break

        application = Application(
            role=role,
            candidate=candidate,
            candidate_match=candidate_match,
            application_time=application_time
        )
        applications.append(application)
        pairs.add((role.role_id, candidate.candidate_id))
    
    db.session.add_all(applications)
    db.session.flush()
    return applications

def generate_interview_data(num_records, applications, interviewers, candidates, skills, main_interviewer=None):
    """Generates synthetic data for the Interview model.

    Args:
        num_records (int): The number of interview records to generate.
        applications (list): A list of Application objects to be associated with the interviews.
        interviewers (list): A list of Account objects representing the interviewers.
        candidates (list): A list of Candidate objects representing the candidates being interviewed.
        skills (list): A list of Skill objects to be assigned skill scores for the interviews.

    Returns:
        list: A list of generated Interview objects.
    """
    stages = [1, 2, 3, 4, 5]
    statuses = [1, 2, 3, 4, 5]

    interviews = []
    for _ in range(num_records):
        interview_time = data_generator.date_time_between(start_date='-1y', end_date='now')
        stage = data_generator.random_element(stages)
        status = data_generator.random_element(statuses)
        duration = data_generator.random_int(min=20*60, max=60*60)
        speaking_time = data_generator.random_int(min=60, max=300)
        wpm = data_generator.random_int(min=100, max=200)
        audio_url = data_generator.url()
        video_url = data_generator.url()
        score = data_generator.random_int(min=0, max=100)
        engagement = data_generator.random_int(min=0, max=100)
        sentiment = data_generator.random_int(min=0, max=100)
        keywords = data_generator.words(nb=5)
        under_review = data_generator.boolean()
        candidate = data_generator.random_element(candidates)
        application = data_generator.random_element(applications)

        interview = Interview(
            interview_time=interview_time,
            stage=stage,
            status=status,
            duration=duration,
            audio_url=audio_url,
            video_url=video_url,
            score=score,
            engagement=engagement,
            sentiment=sentiment,
            keywords=keywords,
            under_review=under_review,
            candidate=candidate,
            applications=application,
            speaking_time=speaking_time,
            wpm=wpm
        )

        interviews.append(interview)

    db.session.add_all(interviews)
    db.session.flush()

    interview_skill_scores = []
    interview_interviewer_speaking = []
    for i in range(num_records):

        interview = interviews[i]
        # Assign random interviewers to the interview
        num_interviewers = data_generator.random_int(min=1, max=3)
        interview_interviewers = data_generator.random_elements(interviewers, length=num_interviewers, unique=True)
        if main_interviewer is not None:
            interview_interviewers.append(main_interviewer)
        
        interview.interviewers.extend(interview_interviewers)

        # Assign random skill scores to the interview
        num_skills = data_generator.random_int(min=1, max=5)
        for skill in data_generator.random_elements(skills, length=num_skills, unique=True):
            score = data_generator.random_int(min=0, max=100)
            
            interview_skill_score = {
                'interview_id': interview.interview_id,
                'skill_id': skill.skill_id,
                'score': score
            }
            interview_skill_scores.append(interview_skill_score)

        # Generate speaking metrics for the interview
        for interviewer in interview_interviewers:
            speaking_time = data_generator.random_int(min=20*60, max=60*60)
            wpm = data_generator.random_int(min=100, max=200)
            interviewer_speaking_metrics = {
                "interview_id": interview.interview_id, 
                "interviewer_id": interviewer.account_id,
                "speaking_time": speaking_time,
                "wpm": wpm
            }
            interview_interviewer_speaking.append(interviewer_speaking_metrics)

    if interview_skill_scores:
        db.session.execute(interview_skill_score_table.insert(), interview_skill_scores)
    if interview_interviewer_speaking:
        db.session.execute(interview_interviewer_speaking_table.insert(), interview_interviewer_speaking)

    db.session.flush()
    return interviews

skill_list = set([
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

def generate_skill_data():
    """Generates Skill objects from a list of skill names.

    Args:
        skills (list): A list of skill names.

    Returns:
        list: A list of generated Skill objects.
    """
    skills = []
    existing_skills = Skill.query.all()
    if len(existing_skills) == len(skill_list):
        return existing_skills
    for skill_name in skill_list:
        skill = Skill(skill_name=skill_name)
        skills.append(skill)

    db.session.add_all(skills)
    db.session.flush()
    return skills

def print_table_entry(table_entry, Model):
    for column, value in table_entry.__dict__.items():
        print(f"{column}: {value}")
    inspector = inspect(Model)
    column_names = [column.name for column in inspector.columns]

    # Iterate over the column names and check if they exist in the instance's __dict__
    for column in column_names:
        if column not in table_entry.__dict__:
            print(f"{column} is missing")
        elif table_entry.__dict__[column] is None:
            print(f"{column} is None")

def generate_synthetic_data(num):
    """Creates synthetic data to add to the database.
    
    Args:
        num (int): The number of entries in each table to create.""" 

    accounts = generate_account_data(num)
    skills = generate_skill_data()
    roles = generate_role_data(num, accounts, skills)
    candidates = generate_candidate_data(num)
    applications = generate_application_data(num, roles, candidates)
    interviews = generate_interview_data(num, applications, accounts, candidates, skills)
    if DEBUG_SYNTHETIC_DATA:
        print_table_entry(accounts[-1], Account)
        print_table_entry(skills[-1], Skill)
        print_table_entry(roles[-1], Role)
        print_table_entry(candidates[-1], Candidate)
        print_table_entry(applications[-1], Application)
        print_table_entry(interviews[-1], Interview)

def generate_synthetic_data_on_account_creation(account_id, num=SYNTHETIC_DATA_ENTRIES, batches=SYNTHETIC_DATA_BATCHES):
    """Creates synthetic data for a new account. 

    Args:
        account_id (int): The account id of the new account.
        num (int): The number of entries to create in each table per batch.
        batches (int): The number of batches to create (so that MetricHistory has data)."""
    
    # Get existing data before generating batches
    skills = Skill.query.all()
    #accounts = Account.query.all()
    accounts = db.session.query(Account).filter(Account.account_type.in_(["Recruiter", "Hiring Manager"])).order_by(func.random()).limit(15).all()
    candidates = Candidate.query.all()
    new_account = Account.query.filter_by(account_id=account_id).first()
    new_roles = []
    new_applications = []
    new_interviews = []

    def generate_batch(account_id, num):
        """Helper function to create one batch of synthetic data for a new account."""

        def generate_rows(generated_data, row_list):
            db.session.add_all(generated_data)
            row_list += generated_data
        
        # Create Roles under the new account
        generate_rows(generate_role_data(num, accounts, skills, new_account), new_roles)
        generate_rows(generate_application_data(num, new_roles, candidates), new_applications)
        generate_rows(generate_interview_data(num, new_applications, accounts, candidates, skills, new_account), new_interviews)
        
    current_date = datetime.now().date()
    days_ago = batches * 6
    for batch_num in range(batches):
        generate_batch(account_id, num)
        if batch_num < batches - 1:
            # Compute and update MetricHistory after each batch
            fitting_job_applications_percentage(account_id)
            metric_history_entry = MetricHistory.query.filter(
                MetricHistory.account_id == account_id,
                MetricHistory.metric_name == 'fitting_job_applications_percentage',
                or_(
                MetricHistory.metric_day == current_date,
                # Handle the case where the date changes during execution
                MetricHistory.metric_day == current_date - timedelta(days=1)
                )
            ).first()
            if metric_history_entry:
                metric_history_entry.metric_day = current_date - timedelta(days=days_ago)
            days_ago -= 6

    db.session.commit()


def fake_interview(interview_num):
    return {
        "id": interview_num,
        "date": get_random_date(),
        "time": get_random_time(),
        "candidateName": data_generator.name(),
        "currentCompany": data_generator.company(),
        "interviewers": data_generator.name() + ", " + data_generator.name(),
        "role": data_generator.job(),
    }


if 'SYNTHETIC' in environ:
    with app.app_context(): 
        generate_synthetic_data(int(environ['SYNTHETIC']))
        db.session.commit()