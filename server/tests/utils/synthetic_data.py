from server.src.routes import sessions 
from server.src.synthetic_data import generate_synthetic_data, generate_synthetic_data_on_account_creation
from server.app import app as flask_app
from server.src.database import Account, db

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