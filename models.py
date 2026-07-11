import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_security import hash_password, UserMixin, RoleMixin
from sqlalchemy import CheckConstraint, text

db = SQLAlchemy()

user_role = db.Table(
    'user_role',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(), default=True)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    roles = db.relationship('Role', secondary='user_role', backref=db.backref('users', lazy='dynamic'))
    blacklist = db.Column(db.Boolean, default=False) # For Admin to blacklist users
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    company_profile = db.relationship('CompanyProfile', backref='user', uselist=False, cascade="all, delete-orphan")

class CompanyProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(100))
    is_approved = db.Column(db.Boolean, default=False)
    placement_drives = db.relationship('PlacementDrive', back_populates='company_profile', lazy=True, cascade="all, delete-orphan")

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=False)
    branch_cgpa = db.Column(db.JSON, nullable=False) # {"branch": cgpa}
    resume = db.Column(db.String(255)) # Path to file
    applications = db.relationship('Application', backref='student', lazy=True)

class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id', ondelete='SET NULL'))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    salary = db.Column(db.Float, CheckConstraint('salary >= 0.0'), nullable=False)
    skills_required = db.Column(db.String(255))
    min_cgpa = db.Column(db.Float, CheckConstraint('min_cgpa >= 0.0 AND min_cgpa <= 10.0'), default=0.0)
    start_date = db.Column(db.DateTime, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), CheckConstraint("status IN ('Pending', 'Approved', 'Closed')"), default='Pending')
    is_approved = db.Column(db.Boolean, default=False)
    company_profile = db.relationship('CompanyProfile', back_populates='placement_drives')
    applications = db.relationship('Application', back_populates='drive', lazy=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id', ondelete='SET NULL'))
    date_applied = db.Column(db.DateTime, server_default=text('CURRENT_TIMESTAMP'))
    status = db.Column(db.String(20), CheckConstraint("status IN ('Applied', 'Shortlisted', 'Selected', 'Rejected')"), default='Applied')
    drive = db.relationship('PlacementDrive', back_populates='applications')

class PlacementResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'))
    salary = db.Column(db.Float, CheckConstraint('salary >= 0.0'), nullable=False)
    joining_date = db.Column(db.DateTime, nullable=False)
    student = db.relationship('StudentProfile', backref='placement_results')
    company = db.relationship('CompanyProfile', backref='placement_results')