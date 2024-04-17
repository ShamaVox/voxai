from .app import app as app
from flask_sqlalchemy import SQLAlchemy

# Insecure; should load password from an environment variable and use a more secure password eventually
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://ubuntu:voxai@localhost:5432/voxai_db"
db = SQLAlchemy(app)

class Account(db.Model):
    email = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    account_type = db.Column(db.String)

    def __repr__(self):
        return f'<Account {self.email}>'

#with app.app_context():
#    db.create_all()