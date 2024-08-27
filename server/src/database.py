from .app import app as app
from flask_sqlalchemy import SQLAlchemy
import datetime
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
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://linux:password@localhost:5432/voxai_db"
db = SQLAlchemy(app)

class Account(db.Model):
    account_id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    email = db.Column(db.String, nullable=False, unique=True)
    name = db.Column(db.String, nullable=False, default="Default Name")
    account_type = db.Column(db.String, nullable=False, default="Recruiter")
    organization = db.Column(db.String, default="Default Company")
    onboarded = db.Column(db.Boolean, nullable=False, default=False) 
    roles = db.relationship('Role', back_populates="direct_manager")
    teammates = db.relationship('Role', secondary="role_teammate", back_populates='teammates')
    interviews = db.relationship("Interview", secondary="interview_interviewer_speaking", back_populates="interviewer_speaking_metrics")
    metric_history = db.relationship("MetricHistory", back_populates="account")

    def __repr__(self):
        return f'<Account {self.email}>'

class Skill(db.Model):
    skill_id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    skill_name = db.Column(db.String, unique=True, nullable=False)
    interviews = db.relationship("Interview", secondary="interview_skill_score", back_populates="skill_scores")
    roles = db.relationship("Role", secondary="role_skill", back_populates="skills")

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
    direct_manager = db.relationship("Account", foreign_keys=[direct_manager_id], back_populates="roles") 

    # Many-to-many relationship for skills and teammates
    applications = db.relationship('Application', back_populates='role')
    teammates = db.relationship('Account', secondary="role_teammate", back_populates='teammates')
    skills = db.relationship('Skill', secondary="role_skill", back_populates='roles')

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
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.candidate_id'), nullable=False)
    candidate_match = db.Column(db.Integer)  # Resume score
    application_time = db.Column(db.DateTime, default=datetime.datetime.now(datetime.UTC))

    role = db.relationship("Role", back_populates="applications")
    candidate = db.relationship("Candidate", back_populates="applications")
    interviews = db.relationship("Interview", back_populates="applications")

    __table_args__ = (db.UniqueConstraint('role_id', 'candidate_id', name='unique_role_candidate'),)

    def __repr__(self):
        return f'<Application {self.application_id} - Role: {self.role.role_name}, Candidate: {self.candidate.candidate_name}>'

class Candidate(db.Model):
    candidate_id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    candidate_name = db.Column(db.String, nullable=False)
    current_company = db.Column(db.String)
    interview_stage = db.Column(db.Integer)  
    resume_url = db.Column(db.String)

    applications = db.relationship("Application", back_populates="candidate", foreign_keys=[Application.candidate_id])
    interviews = db.relationship("Interview", back_populates="candidate")

    def __repr__(self):
        return f'<Candidate {self.candidate_id} - Name: {self.candidate_name}, Company: {self.current_company}>'

class Interview(db.Model):
    interview_id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    application_id = db.Column(db.Integer, db.ForeignKey("application.application_id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidate.candidate_id"), nullable=False)
    interview_time = db.Column(db.DateTime, nullable=False)
    stage = db.Column(db.Integer)  
    status = db.Column(db.Integer)
    duration = db.Column(db.Integer) 
    audio_url = db.Column(db.String)
    video_url = db.Column(db.String)
    audio_url_preprocessed = db.Column(db.String)
    video_url_preprocessed = db.Column(db.String)
    recall_id = db.Column(db.String(36)) # Should be unique eventually, but duplicates can exist for now for testing
    score = db.Column(db.Integer)
    engagement_json = db.Column(db.JSON)
    engagement = db.Column(db.Integer) # Summary score over the entire interview
    sentiment = db.Column(db.Integer) # Summary score over the entire interview
    speaking_time = db.Column(db.Integer)
    wpm = db.Column(db.Integer)
    keywords = db.Column(db.ARRAY(db.String)) 
    under_review = db.Column(db.Boolean)
    summary = db.Column(db.Text)

    # Relationships
    skill_scores = db.relationship("Skill", secondary="interview_skill_score", back_populates="interviews")
    applications = db.relationship("Application", back_populates="interviews") # TODO: change to "application"
    candidate = db.relationship("Candidate", back_populates="interviews")
    interviewer_speaking_metrics = db.relationship("Account", secondary="interview_interviewer_speaking", back_populates="interviews")
    transcript_lines = db.relationship('TranscriptLine', back_populates='interview', order_by='TranscriptLine.start')

    def __repr__(self):
        return f'<Interview {self.interview_id} - Application: {self.application_id}, Time: {self.interview_time}>'

class TranscriptLine(db.Model):
    __tablename__ = 'transcript_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.interview_id'), nullable=False)
    text = db.Column(db.Text)
    start = db.Column(db.Integer)
    end = db.Column(db.Integer)
    confidence = db.Column(db.Float)
    sentiment = db.Column(db.String)
    # TODO: Remove engagement from TranscriptLine
    engagement = db.Column(db.String)
    speaker = db.Column(db.String)
    labels = db.Column(db.Text)

    # Relationships
    interview = db.relationship('Interview', back_populates='transcript_lines')

    def __repr__(self):
        return f'<TranscriptLine {self.id} - Interview: {self.interview_id}, Start: {self.start}>'

# Skill Scores
interview_skill_score_table = db.Table(
    "interview_skill_score",
    db.Column("interview_id", db.Integer, db.ForeignKey("interview.interview_id")),
    db.Column("skill_id", db.Integer, db.ForeignKey("skill.skill_id")),  
    db.Column("score", db.Integer)
)

# Speaking Time and WPM
interview_interviewer_speaking_table = db.Table(
    "interview_interviewer_speaking",
    db.Column("interview_id", db.Integer, db.ForeignKey("interview.interview_id")),
    db.Column("interviewer_id", db.Integer, db.ForeignKey("account.account_id")),
    db.Column("speaking_time", db.Integer),  # in seconds
    db.Column("wpm", db.Integer),
    db.Column("interviewer_notes", db.String), # Notes taken by each interviewer
    db.Column("interviewer_score", db.Integer) # Interviewer's score for the candidate
)

class MetricHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.account_id'), nullable=False)
    metric_name = db.Column(db.String, nullable=False)
    metric_value = db.Column(db.Integer, nullable=False)
    metric_day = db.Column(db.Date, nullable=False)
    account = db.relationship("Account", back_populates="metric_history")

    def __repr__(self):
        return f'<MetricHistory {self.id}>'

    # TODO: Enforce (account_id, metric_name, metric_day) should be unique 