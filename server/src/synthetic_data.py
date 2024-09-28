from faker import Faker
from .database import Account, Role, Application, Candidate, Interview, Skill, MetricHistory, Organization, db, interview_skill_score_table, interview_interviewer_speaking_table
from .utils import get_random_time, get_random_date
from .queries import fitting_job_applications_percentage
from os import environ
from .app import app as app
from sqlalchemy import inspect, or_, func
from .constants import SYNTHETIC_DATA_ENTRIES, SYNTHETIC_DATA_BATCHES, DEBUG_SYNTHETIC_DATA, ENABLE_SYNTHETIC_PREPROCESSING, ENABLE_SYNTHETIC_ENGAGEMENT, ENABLE_SYNTHETIC_SENTIMENT, SYNTHETIC_INTERVIEW_PROCESSING_PERCENTAGE, SKILL_LIST
from .apis import preprocess, get_sentiment, get_engagement
from datetime import datetime, timedelta

data_generator = Faker()

def generate_account_data(num, specified_email=None, specified_account_type=None):
    """Generates synthetic data for the Account model.

    Args:
        num_records (int): The number of account records to generate.
        specified_email (str, optional): A specific email to use for the first account.
        specified_account_type (str, optional): The account type to use for the first account.

    Returns:
        list: A list of generated Account objects.
    """
    account_types = ["Recruiter", "Hiring Manager"]
    accounts = []
    emails = set()

    for i in range(num):
        while True:
            if i == 0 and specified_email:
                email = specified_email
            else:
                email = data_generator.email()
                email = email.split("@")[0] + "_" + data_generator.name() + "_" + data_generator.company() + "@" + email.split("@")[1]
            if email not in emails:
                emails.add(email)
                break

        name = data_generator.name()
        if i == 0 and specified_account_type:
            account_type = specified_account_type
        else:
            account_type = data_generator.random_element(account_types)

        organization_name = data_generator.company()
        organization = Organization(name=organization_name) 
        db.session.add(organization)

        account = Account(
            email=email,
            name=name,
            account_type=account_type,
            organization=organization  
        )
        accounts.append(account)

    db.session.add_all(accounts)
    return accounts

def generate_role_data(num_records, accounts, skills, direct_manager=None):
    """Generates synthetic data for the Role model.

    Args:
        num_records (int): The number of role records to generate.
        accounts (list): A list of Account objects to be used as direct managers and teammates.
        skills (list): A list of Skill objects to be assigned to the roles.
        direct_manager (Account, optional): The Account to use as direct manager for these roles. 

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
    return candidates

def generate_application_data(num_records, roles, candidates, match_threshold=None, fitting_applications=None, percentage_days=None, new_pace_start_date=None, pace=None, old_pace=None):
    """Generates synthetic data for the Application model.

    Args:
        num_records (int): The number of application records to generate.
        roles (list): A list of Role objects to be used as the roles for the applications.
        candidates (list): A list of Account objects representing the candidates who submitted the applications.
        match_threshold (int, optional): Threshold used to generate applications that intentionally do or do not fit the criteria.
        fitting_applications (int, optional): Number of applications that should have a match above match_threshold.
        percentage_days (int, optional): Number of days to generate applications over when pacing applications.
        new_pace_start_date (datetime, optional): The start date for pacing applications at pace instead of old_pace.
        pace (int, optional): The number of days between applications in the new pacing period.
        old_pace (int, optional): The number of days between applications in the old pacing period.

    Returns:
        list: A list of generated Application objects.
    """
    applications = []
    pairs = set()
    if percentage_days is not None: 
        current_date = datetime.now()
        start_date = current_date - timedelta(days=percentage_days)
        num_records = percentage_days
    for i in range(num_records):
        role = data_generator.random_element(roles)
        candidate = data_generator.random_element(candidates)
        if fitting_applications is not None and match_threshold is not None:
            candidate_match = match_threshold + 1 if i < fitting_applications else match_threshold - 1
        else:
            candidate_match = data_generator.random_int(min=0, max=100)
        if percentage_days is not None:
            application_time = start_date + timedelta(days=i-1)
            if (application_time < new_pace_start_date or i % pace != 0) and (application_time < start_date or application_time >= new_pace_start_date or i % old_pace != 0):
                # Skip generating applications that don't have the desired spacing
                continue
        else:
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
        db.session.add(application)
        applications.append(application)
        pairs.add((role.role_id, candidate.candidate_id))
    
    return applications

def generate_interview_data(num_records, applications, interviewers, candidates, skills, main_interviewer=None, pace=None, old_pace=None, new_pace_start_date=None):
    """Generates synthetic data for the Interview model.

    Args:
        num_records (int): The number of interview records to generate.
        applications (list): A list of Application objects to be associated with the interviews.
        interviewers (list): A list of Account objects representing the interviewers.
        candidates (list): A list of Candidate objects representing the candidates being interviewed.
        skills (list): A list of Skill objects to be assigned skill scores for the interviews.
        main_interviewer (Account, optional): The main interviewer for all interviews. Selects a random account if not provided.
        pace (int, optional): When pacing interviews, the number of days between interviews or between application and interview in the new pacing period.
        old_pace (int, optional): When pacing interviews, the number of days between interviews or between application and interview in the old pacing period.
        new_pace_start_date (datetime, optional): The start date for applying the new pacing of interviews.

    Returns:
        list: A list of generated Interview objects.
    """
    stages = [1, 2, 3, 4, 5]
    statuses = [1, 2, 3, 4, 5]

    interviews = []
    if pace:
        num_records = len(applications)
    for n in range(num_records):
        stage = data_generator.random_element(stages)
        status = data_generator.random_element(statuses)
        duration = data_generator.random_int(min=20*60, max=60*60)
        speaking_time = data_generator.random_int(min=60, max=300)
        wpm = data_generator.random_int(min=100, max=200)
        score = data_generator.random_int(min=0, max=100)
        engagement = data_generator.random_int(min=0, max=100)
        sentiment = data_generator.random_int(min=0, max=100)
        keywords = data_generator.words(nb=5)
        under_review = data_generator.boolean()
        candidate = data_generator.random_element(candidates)
        if pace is not None:
            application = applications[n]
            if application.application_time >= new_pace_start_date: 
                interview_time = application.application_time + timedelta(days=pace)
            else:
                interview_time = application.application_time + timedelta(days=old_pace)
        else:
            application = data_generator.random_element(applications)
            interview_time = data_generator.date_time_between(start_date='-1y', end_date='+2m')
        if interview_time < datetime.now() and n % int(100 / SYNTHETIC_INTERVIEW_PROCESSING_PERCENTAGE) == 0:
            audio_url = 's3://voxai-test-audio-video/file_example_MP3_700KB.mp3'
            video_url = 's3://voxai-test-audio-video/file_example_MP4_480_1_5MG.mp4'
        else:
            audio_url = data_generator.url()
            video_url = data_generator.url()

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

    # Preprocess audio and video, then get sentiment and engagement if interview time is in the past
    if ENABLE_SYNTHETIC_PREPROCESSING:
        for interview in interviews:
            if "s3://" not in interview.audio_url and "s3://" not in interview.video_url:
                continue
            if interview.interview_time < datetime.now():
                preprocess_audio = bool(interview.audio_url)
                preprocess_video = bool(interview.video_url)

                # Call the preprocess function
                preprocess(interview, audio=preprocess_audio, video=preprocess_video)

        db.session.flush()

    # Get sentiment and engagement if the interview time is in the past
    if ENABLE_SYNTHETIC_SENTIMENT or ENABLE_SYNTHETIC_ENGAGEMENT:
        for interview in interviews:
            if "s3://" not in interview.audio_url and "s3://" not in interview.video_url:
                continue
            if ENABLE_SYNTHETIC_PREPROCESSING:
                audio_url = interview.audio_url_preprocessed 
                video_url = interview.video_url_preprocessed
            else:
                audio_url = interview.audio_url 
                video_url = interview.video_url 
            if interview.interview_time < datetime.now():
                if video_url: 
                    if ENABLE_SYNTHETIC_SENTIMENT:
                        interview.sentiment = get_sentiment(video_url, video=True)
                    if ENABLE_SYNTHETIC_ENGAGEMENT:
                        interview.engagement = get_engagement(video_url, video=True)
                elif audio_url:
                    if ENABLE_SYNTHETIC_SENTIMENT:
                        interview.sentiment = get_sentiment(audio_url, video=False)
                    if ENABLE_SYNTHETIC_ENGAGEMENT:
                        interview.engagement = get_engagement(audio_url, video=False)

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
        
        interview.interviewer_speaking_metrics.extend(interview_interviewers)

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

    return interviews

def generate_skill_data():
    """Generates Skill objects from a list of skill names.

    Args:
        skills (list): A list of skill names.

    Returns:
        list: A list of generated Skill objects.
    """
    skills = []
    existing_skills = Skill.query.all()
    if len(existing_skills) == len(SKILL_LIST):
        return existing_skills
    for skill_name in SKILL_LIST:
        skill = Skill(skill_name=skill_name)
        skills.append(skill)

    db.session.add_all(skills)
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

def generate_synthetic_data(
    num,
    batches=1,
    generate_accounts=True,
    generate_skills=True,
    generate_roles=True,
    generate_candidates=True,
    generate_applications=True,
    generate_interviews=True,
    generate_metric_history=True,
    account_id=None,
    match_threshold=None,
    fitting_applications=None,
    days=None,
    percentage_days=None,
    pace=None,
    old_pace=None
):
    """
    Creates synthetic data to add to the database with customization options.
    
    Args:
        num (int): The number of entries in each table to create per batch.
        batches (int): The number of batches to create.
        generate_accounts (bool): Whether to generate accounts or query existing ones.
        generate_skills (bool): Whether to generate skills or query existing ones.
        generate_roles (bool): Whether to generate roles or query existing ones.
        generate_candidates (bool): Whether to generate candidates or query existing ones.
        generate_applications (bool): Whether to generate applications or query existing ones.
        generate_interviews (bool): Whether to generate interviews or query existing ones.
        generate_metric_history (bool): Whether to compute and update metric history after each batch.
        account_id (int, optional): The account ID for which to generate data. If provided, the new data will be associated with this account.
        match_threshold (float, optional): The match threshold for generating application data.
        fitting_applications (int, optional): The number of fitting applications to generate.
        days (int, optional): When pacing interviews, the number of days in the new pacing period, extending this number of days back from the current date.
        percentage_days (int, optional): When pacing interviews, the number of days in the old pacing period, extending this number of days back from the current date (excluding the new pacing period).
        pace (int, optional): When pacing interviews, the number of days between interviews or between application and interview in the new pacing period.
        old_pace (int, optional): When pacing interviews, the number of days between interviews or between application and interview in the old pacing period.

    Note:
        When batches > 1, roles, applications, and interviews will always be generated (generate_roles, generate_applications, generate_interviews will be set to True).
    """
    
    accounts = generate_account_data(num) if generate_accounts else db.session.query(Account).filter(Account.account_type.in_(["Recruiter", "Hiring Manager"])).order_by(func.random()).limit(15).all()
    skills = generate_skill_data() if generate_skills else Skill.query.all()
    candidates = generate_candidate_data(num) if generate_candidates else Candidate.query.all()

    new_account = Account.query.filter_by(account_id=account_id).first() if account_id else None

    roles = []
    applications = []
    interviews = []
    if batches > 1:
        # Function does not support generating batches of only some tables
        generate_roles = True 
        generate_applications = True 
        generate_interviews = True 

    if days is not None:
        new_pace_start_date = datetime.now() - timedelta(days=pace + days)
    else:
        new_pace_start_date = None

    def generate_batch(new_account, num, roles, applications, interviews, match_threshold, fitting_applications):
        """Helper function to create one batch of synthetic data for a new account."""
        
        new_roles = generate_role_data(num, accounts, skills, new_account) if generate_roles else Role.query.all()
        new_applications = generate_application_data(num, new_roles, candidates, match_threshold, fitting_applications, percentage_days=percentage_days, new_pace_start_date=new_pace_start_date, pace=pace, old_pace=old_pace) if generate_applications else Application.query.all()
        
        interviews += generate_interview_data(num, new_applications, accounts, candidates, skills, new_account, pace, old_pace, new_pace_start_date) if generate_interviews else Interview.query.all()
        if generate_roles or not roles:
            roles += new_roles 
        if generate_applications or not applications:
            applications += new_applications
        
    if generate_metric_history:
        current_date = datetime.now().date()
        days_ago = batches * 6
    for batch_num in range(batches):
        generate_batch(new_account, num, roles, applications, interviews, match_threshold, fitting_applications)
        if generate_metric_history:
            if batch_num < batches - 1:
                # Compute and update MetricHistory after each batch
                fitting_job_applications_percentage(account_id)
                change_metric_history_day(account_id, "fitting_job_applications_percentage", current_date - timedelta(days=days_ago))
                days_ago -= 6
    if DEBUG_SYNTHETIC_DATA:
        print_table_entries(accounts, skills, roles, candidates, applications, interviews)
    db.session.commit()
    

def generate_synthetic_data_on_account_creation(account_id, num=SYNTHETIC_DATA_ENTRIES, batches=SYNTHETIC_DATA_BATCHES):
    generate_synthetic_data(
        num,
        batches,
        generate_accounts=False,
        generate_skills=False,
        generate_roles=True,
        generate_candidates=False,
        generate_applications=True,
        generate_interviews=True,
        generate_metric_history=True,
        account_id=account_id
    )


def generate_metric_history(account_id, days, target_percentage, target_change):
    """Generates metric history for the 'fitting_job_applications_percentage' metric for a given account.

    This function creates a series of MetricHistory records for the specified account, going back
    a certain number of days from the current date. The metric values are calculated based on the
    target percentage and the target change rate.

    Args:
        account_id (int): The ID of the account for which to generate the metric history.
        days (int): The number of days to generate the metric history for, counting backwards from the current date.
        target_percentage (float): The target percentage for the 'fitting_job_applications_percentage' metric.
        target_change (float): The percentage change to apply to the target percentage for each day in the history.

    Returns:
        None

    The function calculates the metric value for each day by dividing the target percentage by (1 + target_change / 100).
    This adjusts the metric value based on the target change rate.

    The generated MetricHistory records are added to the database session, but the session is not committed.
    It is the responsibility of the calling code to commit the session after generating the metric history."""

    current_day = datetime.now().date()
    for i in range(days):
        past_day = current_day - timedelta(days=i + 1)
        metric_value = target_percentage / (1 + target_change / 100)  # Calculate adjusted metric value
        metric_history = MetricHistory(
            account_id=account_id,
            metric_name="fitting_job_applications_percentage",
            metric_value=metric_value,
            metric_day=past_day
        )
        db.session.add(metric_history)
    
def change_metric_history_day(account_id, metric_name, metric_day):
    """
    Updates the metric day for a specific metric history entry for a given account.

    This function searches for a metric history entry for a given account and metric name
    that matches the current date or the previous day (to account for date changes during execution).
    If an entry is found, it updates the metric day to the provided new date.

    Args:
        account_id (int): The ID of the account whose metric history entry is to be updated.
        metric_name (str): The name of the metric to be updated.
        metric_day (date): The new date to set for the metric history entry.

    Returns:
        None
    """
    current_date = datetime.now().date()
    metric_history_entry = MetricHistory.query.filter(
        MetricHistory.account_id == account_id,
        MetricHistory.metric_name == metric_name,
        or_(
        MetricHistory.metric_day == current_date,
        # Handle the case where the date changes during execution
        MetricHistory.metric_day == current_date - timedelta(days=1)
        )
    ).first()
    if metric_history_entry:
        metric_history_entry.metric_day = metric_day


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