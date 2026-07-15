from flask import Flask, render_template, jsonify, request
from flask_security.utils import hash_password, verify_password, login_user, logout_user
from models import db, User, Role, CompanyProfile, StudentProfile, PlacementDrive, Application, PlacementResult
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, roles_accepted, current_user
from flask_caching import Cache
from workers import celery_init_app
import tasks
from flask_cors import CORS
from datetime import datetime, timedelta
from sqlalchemy import text

app = Flask(__name__, template_folder='vuefrontend', static_folder='vuefrontend', static_url_path='')

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placeportal.db'
app.config['SECRET_KEY'] = "super-secret-key"
app.config['SECURITY_PASSWORD_SALT'] = "super-secret-string-007"
app.config['CACHE_TYPE'] = "RedisCache"
app.config['CACHE_REDIS_URL'] = "redis://localhost:6379/0"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Configure Flask-Security for SPA and APIs
app.config['SECURITY_REDIRECT_BEHAVIOR'] = 'spa'
app.config['SECURITY_FLASH_MESSAGES'] = False
app.config['SECURITY_CSRF_PROTECT_MECHANISMS'] = []
app.config['SECURITY_CSRF_IGNORE_UNREADABLE'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = 'Authentication-Token'

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

@app.before_request
def log_request_info():
    app.logger.info(f"=== BEFORE REQUEST: {request.method} {request.path} ===")
    app.logger.info(f"Cookies: {request.cookies}")
    app.logger.info(f"Authorization Header: {request.headers.get('Authorization')}")
    from flask_security import current_user
    app.logger.info(f"User authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        app.logger.info(f"User email: {current_user.email}, roles: {[r.name for r in current_user.roles]}")

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
        return jsonify({"email": user.email, "role": roles[0] if roles else None, "roles": roles, "id": user.id, "token": user.get_auth_token()})
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
                fs_uniquifier=None, # will trigger default uuid
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
            cache.clear()
            login_user(new_user, remember=True)
            roles = [role.name for role in new_user.roles]
            return jsonify({"email": new_user.email, "role": roles[0] if roles else None, "roles": roles, "id": new_user.id, "token": new_user.get_auth_token()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "Error registering user", "error": str(e)}), 500
# SEARCH FUNCTIONALITY

@app.route('/api/search')
def search():
    q = request.args.get('query', '')
    if not q:
        return jsonify([])

    results = []
    for table in ['fts_user', 'fts_company_profile', 'fts_student_profile', 'fts_placement_drive',
                  'fts_placement_result','fts_application']:
        sql = f"SELECT rowid, * FROM {table} WHERE {table} MATCH :q"
        rows = db.session.execute(text(sql), {'q': q}).mappings().all()
        for r in rows:
            results.append(dict(r))

    return jsonify(results)


# ADMIN ENDPOINTS
@app.route('/api/admin/stats')
@auth_required('session', 'token')
@roles_accepted('Admin')
@cache.cached(timeout=60) # Caching Requirement
def get_stats():
    return jsonify({
        "students": StudentProfile.query.count(),
        "companies": CompanyProfile.query.filter_by(status='Approved').count(),
        "drives": PlacementDrive.query.filter_by(status='Approved').count(),
        "applications": Application.query.filter_by(status='Applied').count()
    })

@app.route('/api/admin/search')
@auth_required('session', 'token')
@roles_accepted('Admin')
@cache.cached(timeout=60) # Caching Requirement
def get_users():
    entries = User.query.all()
    return jsonify([{"id": s.id, "username": s.username, "email":s.email,
                     "role": s.roles[0].name if s.roles else None, "blacklist": s.blacklist} for s in entries])

@app.route('/api/admin/drive')
@auth_required('session', 'token')
@roles_accepted('Admin')
@cache.cached(timeout=60) # Caching Requirement
def get_drive():
    pd_entries = PlacementDrive.query.all()
    return jsonify([{
        "id": d.id,
        "company_id": d.company_id,
        "title": d.title,
        "description": d.description,
        "company": d.company_profile.name,
        "salary": d.salary,
        "skills_required": d.skills_required,
        "start_date": d.start_date.isoformat(),
        "deadline": d.deadline.isoformat(),
        "min_cgpa": d.min_cgpa,
        "status": d.status
    } for d in pd_entries])

@app.route('/api/admin/application')
@auth_required('session', 'token')
@roles_accepted('Admin')
@cache.cached(timeout=60) # Caching Requirement
def get_applications():
    ap_entries = Application.query.all()
    return jsonify([{
        "id": d.id,
        "drive_id": d.drive_id,
        "student_id": d.student_id,
        "date_applied": d.date_applied,
        "status": d.status } for d in ap_entries])


@app.route('/api/admin/pending-companies')
@auth_required('session', 'token')
@roles_accepted('Admin')
def pending_companies():
    companies = CompanyProfile.query.filter_by(status='Pending').all()
    return jsonify([{"id": c.id, "name": c.name} for c in companies])

@app.route('/api/admin/pending-drives')
@auth_required('session', 'token')
@roles_accepted('Admin')
def pending_drives():
    print("Fetching pending drives for admin...")
    drives = PlacementDrive.query.filter_by(status='Pending').all()
    return jsonify([{"id": d.id, "title": d.title, "company": d.company_profile.name} for d in drives])

@app.route('/api/admin/approve-company/<int:id>', methods=['POST'])
@auth_required('session', 'token')
@roles_accepted('Admin')
def approve_company(id):
    comp = CompanyProfile.query.get(id)
    comp.status = 'Approved'
    db.session.commit()
    cache.clear() # Clear stats cache
    return jsonify({"message": "Company Approved"})

@app.route('/api/admin/approve-drive/<int:id>', methods=['POST'])
@auth_required('session', 'token')
@roles_accepted('Admin')
def approve_drive(id):
    drive = PlacementDrive.query.get(id)
    drive.status = 'Approved'
    db.session.commit()
    cache.clear() # Clear stats cache
    return jsonify({"message": "Drive Approved"})

@app.route('/api/admin/reject-company/<int:id>', methods=['POST'])
@auth_required('session', 'token')
@roles_accepted('Admin')
def reject_company(id):
    comp = CompanyProfile.query.get(id)
    comp.status = 'Rejected'
    db.session.commit()
    cache.clear() # Clear stats cache
    return jsonify({"message": "Company Rejected"})

@app.route('/api/admin/reject-drive/<int:id>', methods=['POST'])
@auth_required('session', 'token')
@roles_accepted('Admin')
def reject_drive(id):
    drive = PlacementDrive.query.get(id)
    drive.status = 'Rejected'
    db.session.commit()
    cache.clear() # Clear stats cache
    return jsonify({"message": "Drive rejected"})

@app.route('/api/admin/blacklist-user/<int:id>', methods=['POST'])
@auth_required('session', 'token')
@roles_accepted('Admin')
def blacklist_user(id):
    user = User.query.get(id)
    user.blacklist = not user.blacklist
    db.session.commit()
    cache.clear() # Clear stats cache
    return jsonify({"message": "Student blacklisted"})

@app.route('/api/admin/delete-user/<int:id>', methods=['POST'])
@auth_required('session', 'token')
@roles_accepted('Admin')                                                            
def delete_user(id):
    entry = User.query.filter_by(id=id).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
        cache.clear()
    return jsonify({"message": "User deleted"})

@app.route('/api/admin/delete-company/<int:id>', methods=['POST'])
@auth_required('session', 'token')
@roles_accepted('Admin')                                                            
def delete_company(id):
    entry = User.query.filter_by(id=id).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
        cache.clear()
        return jsonify({"message": "Company deleted"})
    else :
        return jsonify({'message': "Entry not Found"})

# COMPANY ENDPOINTS
@app.route('/api/company/profile', methods=['GET'])
@auth_required('session', 'token')
@roles_accepted('Company')
def get_company_profile():
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify({
        "id": company.id,
        "name": company.name,
        "website": company.website or "",
        "status": company.status
    })

@app.route('/api/company/profile', methods=['POST'])
@auth_required('session', 'token')
@roles_accepted('Company')
def update_company_profile():
    data = request.json
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({"error": "Profile not found"}), 404
    
    company.name = data.get('name', company.name)
    company.website = data.get('website', company.website or "")
    
    if company.status == 'Rejected':
        company.status = 'Pending'
        
    db.session.commit()
    cache.clear()
    return jsonify({
        "message": "Profile updated successfully",
        "company": {
            "id": company.id,
            "name": company.name,
            "website": company.website or "",
            "status": company.status
        }
    })

@app.route('/api/company/drives/<int:id>', methods=['GET'])
@auth_required('session', 'token')
@roles_accepted('Company')
def Drives(id):
    entry = CompanyProfile.query.filter_by(user_id=id).first()
    entries = entry.placement_drives
    if entry:
        return jsonify([{"id":e.id,"title":e.title,"desc":e.description,"salary":e.salary,
                         "status":e.status,"start_date":e.start_date.isoformat() if e.start_date else None,
                         "deadline":e.deadline.isoformat() if e.deadline else None,} for e in entries])
    else :
        return jsonify({'error': "Entry not Found"}), 404

@app.route('/api/company/applications', methods=['GET'])
@auth_required('session', 'token')
@roles_accepted('Company')
def get_company_applications():
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({"error": "Company profile not found"}), 404
    
    drive_ids = [d.id for d in company.placement_drives]
    apps = Application.query.filter(Application.drive_id.in_(drive_ids)).all() if drive_ids else []
    
    result = []
    for app in apps:
        student = app.student
        student_user = student.user if student else None
        drive = app.drive
        result.append({
            "id": app.id,
            "drive_id": app.drive_id,
            "drive_title": drive.title if drive else "Unknown",
            "student_id": app.student_id,
            "student_name": student.name if student else "Unknown",
            "student_email": student_user.email if student_user else "N/A",
            "branch_cgpa": student.branch_cgpa if student else {},
            "resume": student.resume if student else "",
            "status": app.status,
            "feedback": app.feedback or "",
            "interview_time": app.interview_time or "",
            "interview_link": app.interview_link or "",
            "date_applied": app.date_applied.isoformat() if app.date_applied else None
        })
    return jsonify(result)

@app.route('/api/company/applications/<int:app_id>/status', methods=['POST'])
@auth_required('session', 'token')
@roles_accepted('Company')
def update_application_status(app_id):
    data = request.json
    new_status = data.get('status')
    feedback = data.get('feedback', '')
    interview_time = data.get('interview_time', '')
    interview_link = data.get('interview_link', '')
    if new_status not in ['Applied', 'Shortlisted', 'Selected', 'Rejected']:
        return jsonify({"error": "Invalid status"}), 400
        
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({"error": "Company profile not found"}), 404
        
    app_record = Application.query.get(app_id)
    if not app_record:
        return jsonify({"error": "Application not found"}), 404
        
    if app_record.drive.company_id != company.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    app_record.status = new_status
    if feedback is not None:
        app_record.feedback = feedback
    
    if new_status == 'Shortlisted':
        if interview_time is not None:
            app_record.interview_time = interview_time
        if interview_link is not None:
            app_record.interview_link = interview_link
    else:
        # Clear interview details if status is changed to Selected or Rejected
        app_record.interview_time = None
        app_record.interview_link = None
        
    db.session.commit()
    cache.clear()
    return jsonify({"message": f"Application status updated to {new_status}"})

@app.route('/api/company/create-drive', methods=['POST'])
@auth_required('session', 'token')
@roles_accepted('Company')
def create_drive():
    data = request.json
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    print(f"Company: {company}, Approved: {company.status if company else 'N/A'}")  # Debugging line
    if not company or not(company.status == 'Approved'):
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
        cache.clear()
        return jsonify({"message": "Drive submitted for Admin approval"}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error creating drive: {e}")  # Debugging line
        return jsonify({"message": "Error creating drive", "error": str(e)}), 500

@app.route('/api/company/drives/<int:id>/status', methods=['POST'])
@auth_required('session', 'token')
@roles_accepted('Company')
def update_drive_status_route(id):
    data = request.json
    new_status = data.get('status')
    if new_status not in ['Approved', 'Closed']:
        return jsonify({"error": "Invalid status"}), 400
    
    drive = PlacementDrive.query.get(id)
    if not drive:
        return jsonify({"error": "Drive not found"}), 404
        
    company = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if not company or drive.company_id != company.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    drive.status = new_status
    db.session.commit()
    cache.clear()
    return jsonify({"message": f"Placement drive status updated to {new_status}"})

# STUDENT ENDPOINTS
@app.route('/api/student/drives')
@auth_required('session', 'token')
@roles_accepted('Student')
def get_student_drives():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first()
    applied_drive_ids = set()
    if student:
        applied_drive_ids = {app.drive_id for app in student.applications}
        
    drives = PlacementDrive.query.filter_by(status='Approved').all()
    return jsonify([{
        "id": d.id, "company_id": d.company_id, "title": d.title, "description": d.description,
        "company": d.company_profile.name if d.company_profile else "Unknown", "salary": d.salary, "skills_required": d.skills_required,
        "start_date": d.start_date.isoformat(), "deadline": d.deadline.isoformat(),
        "min_cgpa": d.min_cgpa,
        "applied": d.id in applied_drive_ids
    } for d in drives])

@app.route('/api/student/applications', methods=['GET'])
@auth_required('session', 'token')
@roles_accepted('Student')
def get_student_applications():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({"error": "Student profile not found"}), 404
    
    result = []
    for app in student.applications:
        drive = app.drive
        result.append({
            "id": app.id,
            "drive_id": app.drive_id,
            "drive_title": drive.title if drive else "Unknown",
            "company_name": drive.company_profile.name if (drive and drive.company_profile) else "Unknown",
            "salary": drive.salary if drive else 0,
            "status": app.status,
            "feedback": app.feedback or "",
            "interview_time": app.interview_time or "",
            "interview_link": app.interview_link or "",
            "date_applied": app.date_applied.isoformat() if app.date_applied else None
        })
    return jsonify(result)

@app.route('/api/student/apply', methods=['POST'])
@auth_required('session', 'token')
@roles_accepted('Student')
def apply():
    data = request.json
    try:
        student = StudentProfile.query.filter_by(user_id=data['user_id']).first()
        drive = PlacementDrive.query.get(data['drive_id'])    
        new_app = Application(student_id=student.id, drive_id=drive.id)
        db.session.add(new_app)
        db.session.commit()
        cache.clear()
        return jsonify({"message": "Application Successful"}), 201
    except:
        db.session.rollback()
        return jsonify({"error": "Entry already exists"}), 400

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

if __name__ == '__main__':
    create_admin()
    app.run(debug=True)