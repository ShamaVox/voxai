from server.src.routes import sessions 
from server.src.synthetic_data import generate_synthetic_data, generate_synthetic_data_on_account_creation, data_generator, generate_account_data, generate_skill_data, generate_role_data, generate_candidate_data, generate_application_data, generate_interview_data, generate_metric_history
from server.app import app as flask_app
from server.src.database import Account, Role, Application, Candidate, MetricHistory, Interview, db
from datetime import datetime, timedelta

# Functions in this file are only used during unit testing and not during regular execution or integration testing.

def create_synthetic_data(num):
    with flask_app.app_context():
        generate_synthetic_data(10)
        db.session.commit()

def create_test_account_and_set_token(client, email, token):
    with flask_app.app_context():
        create_synthetic_data(10)
        account = generate_account_data(1, specified_email=email)[0]
        db.session.commit()
        generate_synthetic_data_on_account_creation(account.account_id)
        sessions[token] = account.account_id
    client.set_cookie('authToken', token)

def create_synthetic_data_for_fitting_percentage(match_threshold, days, target_percentage, target_change):
    # Calculate required number of fitting and total applications
    total_applications = 100  
    fitting_applications = round(total_applications * target_percentage / 100)
    with flask_app.app_context():
        skills = generate_skill_data()
        accounts = generate_account_data(10, None, "Hiring Manager")
        manager = accounts[0]
        roles = generate_role_data(total_applications, accounts, skills, direct_manager=manager)

        # Generate candidates
        candidates = generate_candidate_data(total_applications)

        # Generate applications with controlled match scores
        generate_application_data(total_applications, roles, candidates, match_threshold, fitting_applications)

        # Create historical data for percentage change calculation
        generate_metric_history(manager.account_id, days, target_percentage, target_change)
        db.session.commit()

        return manager.account_id


def create_synthetic_data_for_average_interview_pace(current_user_id, days, percentage_days, expected_average_pace, expected_percentage_change):
    # Create synthetic data for the test
    account = Account(account_id=current_user_id)
    db.session.add(account)

    current_date = datetime.now().date()
    start_date = current_date - timedelta(days=days)
    percentage_start_date = current_date - timedelta(days=percentage_days)

    # Create interviews for the last N days
    for i in range(days):
        interview_time = start_date + timedelta(days=i)
        application = Application(application_time=interview_time - timedelta(days=1))
        db.session.add(application)
        interview = Interview(applications=application, interview_time=interview_time)
        interview.interviewer_speaking_metrics.append(account)
        db.session.add(interview)

    # Create interviews for the last M days excluding the last N days
    for i in range(percentage_days - days):
        interview_time = percentage_start_date + timedelta(days=i)
        application = Application(application_time=interview_time - timedelta(days=1))
        db.session.add(application)
        interview = Interview(applications=application, interview_time=interview_time)
        interview.interviewer_speaking_metrics.append(account)
        db.session.add(interview)

    db.session.commit()

    return current_user_id