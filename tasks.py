from workers import celery_init_app
from celery import shared_task
from models import db, Application, StudentProfile, PlacementDrive
import csv
import os

@shared_task(ignore_result=False)
def export_applications_csv(user_id):
    student = StudentProfile.query.filter_by(user_id=user_id).first()
    apps = Application.query.filter_by(student_id=student.id).all()
    
    # Create export folder if not exists
    if not os.path.exists('static/exports'):
        os.makedirs('static/exports')
        
    filename = f'static/exports/applications_{user_id}.csv'
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Drive Title", "Status"])
        for a in apps:
            drive = PlacementDrive.query.get(a.drive_id)
            writer.writerow([drive.title, a.status])
            
    return filename

@shared_task
def monthly_activity_report():
    # Logic to generate HTML and send email to Admin
    print("Monthly Report Generated for Admin")
    return True