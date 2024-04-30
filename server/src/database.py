from .app import app as app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from os import environ

EXPERIENCE_LEVELS = {
    0: "Entry",
    1: "Junior",
    2: "Mid",
    3: "Senior",
    4: "Staff"
}

CANDIDATE_STATUS = {
    0: "Active",
    1: "Reviewing",
    2: "Hired",
    3: "Rejected"
}

# Insecure; should load password from an environment variable and use a more secure password eventually
if 'TEST' in environ:
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://ubuntu:voxai@localhost:5432/voxai_db_integration_test"
    print("Server using integration test database")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://ubuntu:voxai@localhost:5432/voxai_db"
db = SQLAlchemy(app)

class Account(db.Model):
    account_id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    email = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False, default="Default Name")
    account_type = db.Column(db.String, nullable=False, default="Recruiter")
    organization = db.Column(db.String, default="Default Company")

    def __repr__(self):
        return f'<Account {self.email}>'

class Skill(db.Model):
    skill_id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    skill_name = db.Column(db.String, unique=True, nullable=False)

    def __repr__(self):
        return f'<Skill {self.skill_name}>'

class Role(db.Model):
    role_id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    role_name = db.Column(db.String, nullable=False)
    base_compensation_min = db.Column(db.Integer)
    base_compensation_max = db.Column(db.Integer)
    target_compensation = db.Column(db.Integer)
    experience_level = db.Column(db.Integer)
    years_of_experience_min = db.Column(db.Integer)
    years_of_experience_max = db.Column(db.Integer) 
    target_years_of_experience = db.Column(db.Integer)
    direct_manager_id = db.Column(db.Integer, db.ForeignKey('account.account_id'))
    direct_manager = db.relationship("Account", backref="managed_roles", foreign_keys=[direct_manager_id]) 

    # Many-to-many relationship for skills and teammates
    skills = db.relationship('Skill', secondary="role_skill", backref='roles')
    teammates = db.relationship('Account', secondary="role_teammate", backref='roles')

    def __repr__(self):
        return f'<Role {self.role_name}>'

# Skills for each role
role_skill_table = db.Table('role_skill', db.Model.metadata,
    db.Column('role_id', db.Integer, db.ForeignKey('role.role_id')),
    db.Column('skill_id', db.Integer, db.ForeignKey('skill.skill_id'))
)

# Teammates for each role
role_teammate_table = db.Table('role_teammate', db.Model.metadata,
    db.Column('role_id', db.Integer, db.ForeignKey('role.role_id')),
    db.Column('teammate_id', db.Integer, db.ForeignKey('account.account_id'))
)

class Application(db.Model):
    application_id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.role_id'), nullable=False)
    candidate_email = db.Column(db.String, db.ForeignKey('account.email'), nullable=False)
    candidate_match = db.Column(db.Integer)  # Resume score
    application_time = db.Column(db.DateTime, default=datetime.utcnow)

    role = db.relationship("Role", backref="applications")
    candidate = db.relationship("Account", backref="application")
    interviews = db.relationship("Interview", backref="application")

    __table_args__ = (db.UniqueConstraint('role_id', 'candidate_email', name='unique_role_candidate'),)

    def __repr__(self):
        # TODO: implement
        pass 

class Candidate(db.Model):
    candidate_id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    candidate_name = db.Column(db.String, nullable=False)
    current_company = db.Column(db.String)
    interview_stage = db.Column(db.Integer)  
    resume_url = db.Column(db.String)

    applications = db.relationship("Application", backref="candidate")

    def __repr__(self):
        # TODO: Implement
        pass

class Interview(db.Model):
    interview_id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    application_id = db.Column(db.Integer, db.ForeignKey("application.application_id"), nullable=False)
    interview_time = db.Column(db.DateTime, nullable=False)
    stage = db.Column(db.Integer)  
    status = db.Column(db.Integer)
    duration = db.Column(db.Integer) 
    audio_url = db.Column(db.String)
    video_url = db.Column(db.String)
    score = db.Column(db.Integer)
    engagement = db.Column(db.Integer)
    sentiment = db.Column(db.Integer)
    skill_scores = db.relationship("Skill", secondary="interview_skill_score", backref="interview")
    speaking_metrics = db.relationship("Candidate", secondary="interview_speaking", backref="interview")
    keywords = db.Column(db.ARRAY(db.String)) 
    under_review = db.Column(db.Boolean)

    # Relationships
    application = db.relationship("Application", backref="interview")
    interviewers = db.relationship("Account", secondary="interview_interviewer", backref="interview")
    candidate = db.relationship("Candidate", backref="interview")  # Assuming Candidate table exists 

    def __repr__(self):
        # TODO: Implement
        pass

# Skill Scores
interview_skill_score_table = db.Table(
    "interview_skill_score",
    db.Column("interview_id", db.Integer, db.ForeignKey("interview.interview_id")),
    db.Column("skill_name", db.Integer, db.ForeignKey("skill.skill_id")),  
    db.Column("score", db.Integer)
)

interview_interviewer_table = db.Table(
    "interview_interviewer",
    db.Column("interview_id", db.Integer, db.ForeignKey("interview.interview_id")),
    db.Column("interviewer_email", db.String, db.ForeignKey("account.email")),
    db.Column("candidate_score", db.Integer) # Interviewer's scoring of the candidate
)

# Speaking Time and WPM
interview_speaking_table = db.Table(
    "interview_speaking", 
    db.Column("interview_id", db.Integer, db.ForeignKey("interview.interview_id")),
    db.Column("interviewer_id", db.Integer, db.ForeignKey("account.account_id")), 
    db.Column("candidate_id", db.Integer, db.ForeignKey("candidate.candidate_id")), 
    db.Column("speaking_time", db.Integer),  # in seconds 
    db.Column("wpm", db.Integer)
)


