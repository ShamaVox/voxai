from server.src.routes import sessions 
from server.src.synthetic_data import generate_synthetic_data, generate_synthetic_data_on_account_creation, data_generator
from server.app import app as flask_app
from server.src.database import Account, Role, Application, Candidate, MetricHistory, db
from datetime import datetime, timedelta

def create_synthetic_data(num):
    with flask_app.app_context():
        generate_synthetic_data(10)
        db.session.commit()

def create_test_account_and_set_token(client, email, token):
    with flask_app.app_context():
        create_synthetic_data(10)
        account = Account(email=email)
        db.session.add(account)
        db.session.commit()
        generate_synthetic_data_on_account_creation(account.account_id)
        sessions[token] = account.account_id
    client.set_cookie('authToken', token)

def create_synthetic_data_for_fitting_percentage(match_threshold, days, target_percentage, target_change):
    # Calculate required number of fitting and total applications
    total_applications = 100  
    fitting_applications = int(total_applications * target_percentage / 100)

    # Create a manager account
    manager = Account(email="manager-" + data_generator.name().replace(" ","") + "@example.com", name="Manager", account_type="Manager")
    db.session.add(manager)
    db.session.flush()

    # Create roles and applications with controlled match scores
    for i in range(total_applications):
        role = Role(role_name=f"Role {i}", direct_manager=manager)
        application = Application(
            role=role,
            candidate=Candidate(candidate_name=f"Candidate {i}"),
            candidate_match=match_threshold + 1 if i < fitting_applications else match_threshold - 1
        )
        db.session.add(role)
        db.session.add(application)

    db.session.flush()

    # Create historical data for percentage change calculation
    current_day = datetime.now().date()
    for i in range(days):
        past_day = current_day - timedelta(days=i + 1)
        metric_history = MetricHistory(
            account_id=manager.account_id, 
            metric_name="fitting_job_applications_percentage",
            metric_value=target_percentage / ((1 + target_change/100)),  
            metric_day=past_day
        )
        db.session.add(metric_history)

    db.session.commit()

    return manager.account_id