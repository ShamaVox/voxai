from server.src.sessions import sessions 
from server.src.synthetic_data import generate_synthetic_data, generate_synthetic_data_on_account_creation, data_generator, generate_account_data, generate_skill_data, generate_role_data, generate_candidate_data, generate_application_data, generate_interview_data, generate_metric_history
from server.app import app as flask_app
from server.src.database import Account, Role, Application, Candidate, MetricHistory, Interview, db
from datetime import datetime, timedelta

# Functions in this file are only used during unit testing and not during regular execution or integration testing.

def create_synthetic_data(num, batches=1):
    with flask_app.app_context():
        generate_synthetic_data(num, batches)
        db.session.commit()

def create_test_account_and_set_token(client, email, token, num, batches):
    with flask_app.app_context():
        create_synthetic_data(num, batches)
        account = generate_account_data(1, specified_email=email)[0]
        db.session.commit()
        generate_synthetic_data_on_account_creation(account.account_id, num, batches)
        sessions[token] = account.account_id
    client.set_cookie('authToken', token)

def create_synthetic_data_for_fitting_percentage(match_threshold, days, target_percentage, target_change):
    # Calculate required number of fitting and total applications
    total_applications = 100  
    fitting_applications = round(total_applications * target_percentage / 100)
    with flask_app.app_context():
        accounts = generate_account_data(10, None, "Hiring Manager")
        manager = accounts[0]
        db.session.flush()
        generate_synthetic_data(num=100, batches=1, generate_accounts=False, generate_skills=True, generate_roles=True, generate_candidates=True, generate_applications=True, generate_interviews=False, generate_metric_history=False, account_id=manager.account_id, match_threshold=match_threshold, fitting_applications=fitting_applications)
        # Create historical data for percentage change calculation
        generate_metric_history(manager.account_id, days, target_percentage, target_change)
        db.session.commit()

        return manager.account_id

def create_synthetic_data_for_average_interview_pace(days, percentage_days, expected_average_pace, expected_percentage_change):
    # Create synthetic data for the test
    with flask_app.app_context():
        # TODO: use_first_account_id argument to gen_synthetic_data
        accounts = generate_account_data(10, None, "Hiring Manager")
        db.session.flush()
        current_user_id = accounts[0].account_id

        generate_synthetic_data(num=100, batches=1, generate_accounts=False, generate_skills=True, generate_roles=True, generate_candidates=True, generate_applications=True, generate_interviews=True, generate_metric_history=True, account_id=current_user_id, days=days, percentage_days=percentage_days, pace=expected_average_pace, old_pace=int(expected_average_pace / (1 + expected_percentage_change/100)))

        db.session.commit()

    return current_user_id