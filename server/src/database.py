from .app import app as app
from flask_sqlalchemy import SQLAlchemy
from flask_alembic import Alembic

# Insecure; should load password from an environment variable and use a more secure password eventually
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://ubuntu:voxai@localhost:5432/voxai_db"
db = SQLAlchemy(app)

class Account(db.Model):
    email = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False, default="Default Name")
    account_type = db.Column(db.String, nullable=False, default="Recruiter")
    organization = db.Column(db.String, default="VoxAI")

    def __repr__(self):
        return f'<Account {self.email}>'

# Alembic setup
"""
with app.app_context():
    alembic = Alembic(app)
    alembic.revision(message="Add organization and defaults")
    alembic.upgrade()"""