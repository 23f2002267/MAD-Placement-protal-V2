from flask import Flask, render_template, jsonify, request
from flask_security.utils import hash_password, verify_password
from flask_login import LoginManager, login_required, login_user, logout_user
from models import db, User, Role, CompanyProfile, StudentProfile, PlacementDrive, Application, PlacementResult
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, roles_accepted, current_user
from flask_caching import Cache
from workers import celery_init_app
import tasks
from flask_cors import CORS
from datetime import datetime, timedelta


app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placeportal.db'
app.config['SECRET_KEY'] = "super-secret-key"
app.config['SECURITY_PASSWORD_SALT'] = "super-secret-string-007"
app.config['CACHE_TYPE'] = "RedisCache"
app.config['CACHE_REDIS_URL'] = "redis://localhost:6379/0"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30) # added this to check

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Init Extensions
db.init_app(app)
CORS(app)
cache = Cache(app)

app.config.update(
    CELERY=dict(
        broker_url="redis://localhost:6379/1",
        result_backend="redis://localhost:6379/2",
        task_ignore_result=False,
    ),
)

from workers import celery_init_app
celery_app = celery_init_app(app)
# --- ROLE-BASED API ENDPOINTS ---

@app.route('/')
def index():
    return render_template('index.html')

# LOGOUT 
@app.route('/api/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

# AUTHENTICATION
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and verify_password(data['password'], user.password):
        login_user(user, remember=True)
        print(f"User {user.email} with role {user.roles[0].name if user.roles else 'N/A'} logged in successfully.")
        print(f"Current user roles: {[r.name for r in current_user.roles]}")
        roles = [role.name for role in user.roles]
        return jsonify({"email": user.email, "role": roles[0] if roles else None, "roles": roles, "id": user.id})
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user:
        return jsonify({"message": "User already exists"}), 400
    else:
        try:
            role_obj = Role.query.filter_by(name=data['role']).first()
            if not role_obj:
                return jsonify({"message": "Invalid role"}), 400

            hashed_password = hash_password(data['password'])
            new_user = User(
                username=data['name'],
                email=data['email'],
                password=hashed_password,
                active=True,
                roles=[role_obj],
                blacklist=False,
            )
            db.session.add(new_user)
            db.session.commit()
            if data['role'] == 'Student':
                student_profile = StudentProfile(user_id=new_user.id, name=data['name'], branch_cgpa={})
                db.session.add(student_profile)
            else:
                company_profile = CompanyProfile(user_id=new_user.id, name=data['name'])
                db.session.add(company_profile)
            db.session.commit()
            return jsonify({"message": "User registered successfully"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "Error registering user", "error": str(e)}), 500

# ADMIN ENDPOINTS
@app.route('/api/admin/stats')
@auth_required('session')
@roles_accepted('Admin')
@cache.cached(timeout=60) # Caching Requirement
def get_stats():
    return jsonify({
        "students": StudentProfile.query.count(),
        "companies": CompanyProfile.query.count(),
        "drives": PlacementDrive.query.count()
    })
@app.route('/api/admin/pending-companies')
@auth_required('session')
@roles_accepted('Admin')
def pending_companies():
    companies = CompanyProfile.query.filter_by(is_approved=False).all()
    return jsonify([{"id": c.id, "name": c.name} for c in companies])

@app.route('/api/admin/pending-drives')
@auth_required('session')
@roles_accepted('Admin')
def pending_drives():
    print("Fetching pending drives for admin...")
    drives = PlacementDrive.query.filter_by(status='Pending').all()
    return jsonify([{"id": d.id, "title": d.title, "company": d.company_profile.name} for d in drives])

@app.route('/api/admin/approve-company/<int:id>', methods=['POST'])
@auth_required('session')
@roles_accepted('Admin')
def approve_company(id):
    comp = CompanyProfile.query.get(id)
    comp.is_approved = True
    db.session.commit()
    cache.clear() # Clear stats cache
    return jsonify({"message": "Company Approved"})

@app.route('/api/admin/approve-drive/<int:id>', methods=['POST'])
@auth_required('session')
@roles_accepted('Admin')
def approve_drive(id):
    drive = PlacementDrive.query.get(id)
    drive.status = 'Approved'
    db.session.commit()
    cache.clear() # Clear stats cache
    return jsonify({"message": "Drive Approved"})

# COMPANY ENDPOINTS
@app.route('/api/company/create-drive', methods=['POST'])
@auth_required('session')
@roles_accepted('Company')
def create_drive():
    data = request.json
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    print(f"Company: {company}, Approved: {company.is_approved if company else 'N/A'}")  # Debugging line
    if not company or not company.is_approved:
        return jsonify({"message": "Company not approved by Admin"}), 403
    
    try:
        new_drive = PlacementDrive(
            company_id=company.id,
            title=data['title'],
            description=data['desc'],
            salary=data['salary'],
            skills_required=data['skills_required'],
            min_cgpa=data['min_cgpa'],
            start_date=datetime.fromisoformat(data['start_date']),
            deadline=datetime.fromisoformat(data['deadline'])
        )
        db.session.add(new_drive)
        db.session.commit()
        return jsonify({"message": "Drive submitted for Admin approval"}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error creating drive: {e}")  # Debugging line
        return jsonify({"message": "Error creating drive", "error": str(e)}), 500

# STUDENT ENDPOINTS
@app.route('/api/student/drives')
@auth_required('session')
@roles_accepted('Student')
def get_student_drives():
    drives = PlacementDrive.query.filter_by(status='Approved').all()
    return jsonify([{
        "id": d.id, "title": d.title, "company": d.company.name, 
        "min_cgpa": d.min_cgpa, "description": d.description
    } for d in drives])

@app.route('/api/student/apply', methods=['POST'])
@auth_required('session')
@roles_accepted('Student')
def apply():
    data = request.json
    # Logic to check eligibility
    student = StudentProfile.query.filter_by(user_id=data['user_id']).first()
    drive = PlacementDrive.query.get(data['drive_id'])
    
    if student.cgpa < drive.min_cgpa:
        return jsonify({"message": "Ineligible: CGPA too low"}), 400
    
    new_app = Application(student_id=student.id, drive_id=drive.id)
    db.session.add(new_app)
    db.session.commit()
    return jsonify({"message": "Application Successful"})

@app.route('/api/student/export-csv/<int:user_id>')
def trigger_export(user_id):
    # CELERY ASYNC JOB TRIGGER
    tasks.export_applications_csv.delay(user_id)
    return jsonify({"message": "Export started. You will be notified via chat."})

def create_roles():
    for role_name in ['Admin', 'Company', 'Student']:
        if not Role.query.filter_by(name=role_name).first():
            db.session.add(Role(name=role_name))
    db.session.commit()


def create_admin():
    with app.app_context():
        create_roles()
        admin_role = Role.query.filter_by(name='Admin').first()
        admin = User.query.filter_by(email='admin@placeport.com').first()
        if not admin:
            admin = User(
                username='Admin',
                email='admin@placeport.com',
                password=hash_password('pass'),
                active=True,
                roles=[admin_role],
                blacklist=False
            )
            db.session.add(admin)
            db.session.commit()

with app.app_context():
    admin_role = Role.query.filter_by(name='Admin').first()
    print(admin_role)  # should not be None
    admin_user = User.query.filter(User.roles.contains(admin_role)).first()
    print(admin_user)  # should be your admin user

if __name__ == '__main__':
    create_admin()
    app.run(debug=True)