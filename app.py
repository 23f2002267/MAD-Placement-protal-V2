from flask import Flask, render_template, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager
from models import db, User, Role, CompanyProfile, StudentProfile, PlacementDrive, Application, PlacementResult
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, roles_accepted
from flask_caching import Cache
from workers import celery_init_app
import tasks
from flask_cors import CORS
from datetime import date, timedelta


app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placeportal.db'
app.config['SECRET_KEY'] = "super-secret-key"
app.config['SECURITY_PASSWORD_SALT'] = "salt"
app.config['CACHE_TYPE'] = "RedisCache"
app.config['CACHE_REDIS_URL'] = "redis://localhost:6379/0"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30) # added this to check


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

# AUTHENTICATION (Simplified for your demo)
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and check_password_hash(user.password, data['password']): # Use hash_password in production
        role = user.role[0].name
        return jsonify({"email": user.email, "role": role, "id": user.id})
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user:
        return jsonify({"message": "User already exists"}), 400
    else:
        try:
            hashed_password = generate_password_hash(data['password'])
            new_user = User(username=data['name'], email=data['email'], password=hashed_password, role=[Role.query.filter_by(name=data['role']).first()])
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"message": "User registered successfully"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "Error registering user", "error": str(e)}), 500

# ADMIN ENDPOINTS
@app.route('/api/admin/stats')
@cache.cached(timeout=60) # Caching Requirement
def get_stats():
    return jsonify({
        "students": StudentProfile.query.count(),
        "companies": CompanyProfile.query.count(),
        "drives": PlacementDrive.query.count()
    })

@app.route('/api/admin/pending-companies')
def pending_companies():
    companies = CompanyProfile.query.filter_by(is_approved=False).all()
    return jsonify([{"id": c.id, "name": c.name} for c in companies])

@app.route('/api/admin/approve-company/<int:id>', methods=['POST'])
def approve_company(id):
    comp = CompanyProfile.query.get(id)
    comp.is_approved = True
    db.session.commit()
    cache.clear() # Clear stats cache
    return jsonify({"message": "Company Approved"})

# COMPANY ENDPOINTS
@app.route('/api/company/create-drive', methods=['POST'])
def create_drive():
    data = request.json
    company = CompanyProfile.query.filter_by(user_id=data['user_id']).first()
    if not company or not company.is_approved:
        return jsonify({"message": "Company not approved by Admin"}), 403
    
    new_drive = PlacementDrive(
        company_id=company.id,
        title=data['title'],
        description=data['description'],
        min_cgpa=data['min_cgpa'],
        status='Pending'
    )
    db.session.add(new_drive)
    db.session.commit()
    return jsonify({"message": "Drive submitted for Admin approval"})

# STUDENT ENDPOINTS
@app.route('/api/student/drives')
def get_student_drives():
    drives = PlacementDrive.query.filter_by(status='Approved').all()
    return jsonify([{
        "id": d.id, "title": d.title, "company": d.company.name, 
        "min_cgpa": d.min_cgpa, "description": d.description
    } for d in drives])

@app.route('/api/student/apply', methods=['POST'])
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

def create_admin():
    with app.app_context():
        admin_role = Role.query.filter_by(name='Admin').first()
        admin = User.query.filter_by(email='admin@placeport.com').first()
        if not admin:
            admin = User(
                username='Admin',
                email='admin@placeport.com',
                password=generate_password_hash('pass'),
                active=True,
                role=[admin_role],
                blacklist=False
                )
            
            db.session.add(admin)
            db.session.commit() 

if __name__ == '__main__':
    create_admin()
    app.run(debug=True)