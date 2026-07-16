from celery import shared_task
from models import db, Application, StudentProfile, PlacementDrive, CompanyProfile, User, Notification
import csv
import os
from datetime import datetime

@shared_task(ignore_result=False)
def export_student_history_task(user_id):
    student = StudentProfile.query.filter_by(user_id=user_id).first()
    if not student:
        return "Student not found"
        
    apps = Application.query.filter_by(student_id=student.id).all()
    
    # directory exists
    os.makedirs('static/exports', exist_ok=True)
    filename = f'static/exports/student_{user_id}_history.csv'
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Drive Title", "Company Name", "Salary Offered ($)", "Status", "Interview Time", "Interview Link", "Date Applied"])
        for app in apps:
            drive = app.drive
            company_name = drive.company_profile.name if (drive and drive.company_profile) else "N/A"
            drive_title = drive.title if drive else "N/A"
            salary = drive.salary if drive else 0
            writer.writerow([
                drive_title,
                company_name,
                salary,
                app.status,
                app.interview_time or "N/A",
                app.interview_link or "N/A",
                app.date_applied.strftime("%Y-%m-%d %H:%M:%S") if app.date_applied else "N/A"
            ])
            
    #alert notification
    notification = Notification(
        user_id=user_id,
        message="Your application and placement history export is complete! Ready for download.",
        link=f"/api/exports/student_{user_id}_history.csv"
    )
    db.session.add(notification)
    db.session.commit()
    return filename


@shared_task(ignore_result=False)
def export_company_history_task(user_id):
    company = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not company:
        return "Company profile not found"
        
    # drives of this company
    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    drive_ids = [d.id for d in drives]
    
    apps = Application.query.filter(Application.drive_id.in_(drive_ids)).all() if drive_ids else []
    
    os.makedirs('static/exports', exist_ok=True)
    filename = f'static/exports/company_{user_id}_history.csv'
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Placement Drive", "Candidate Name", "Candidate Email", "Status", "Interview Scheduled", "Feedback Note", "Date Applied"])
        for app in apps:
            student = app.student
            student_user = student.user if student else None
            student_email = student_user.email if student_user else "N/A"
            student_name = student.name if student else "Unknown Candidate"
            drive_title = app.drive.title if app.drive else "N/A"
            writer.writerow([
                drive_title,
                student_name,
                student_email,
                app.status,
                app.interview_time or "N/A",
                app.feedback or "N/A",
                app.date_applied.strftime("%Y-%m-%d %H:%M:%S") if app.date_applied else "N/A"
            ])
            
    #alert notification
    notification = Notification(
        user_id=user_id,
        message="Your placement and applicant history export is complete! Ready for download.",
        link=f"/api/exports/company_{user_id}_history.csv"
    )
    db.session.add(notification)
    db.session.commit()
    return filename


@shared_task
def send_interview_reminders():
    # shortlisted candidates with scheduled interviews
    shortlisted_apps = Application.query.filter(
        Application.status == 'Shortlisted',
        Application.interview_time != None,
        Application.interview_time != ''
    ).all()
    
    os.makedirs('static/logs', exist_ok=True)
    reminders_log = 'static/logs/reminders.log'
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    count = 0
    for app in shortlisted_apps:
        student = app.student
        if not student:
            continue
        student_user = student.user
        if not student_user:
            continue
            
        drive = app.drive
        if not drive:
            continue
        company = drive.company_profile
        company_name = company.name if company else "N/A"
        
        # check if we already sent a notification for this interview time
        existing_notif = Notification.query.filter(
            Notification.user_id == student_user.id,
            Notification.message.like(f"%Interview Reminder%for%{drive.title}%")
        ).first()
        
        if existing_notif:
            continue
            
        # log simulated notifications
        with open(reminders_log, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] === INTERVIEW REMINDER SENT ===\n")
            f.write(f"[EMAIL] To: {student_user.email} | Subject: Interview Scheduled: {drive.title} with {company_name}\n")
            f.write(f"        Body: Dear {student.name}, this is a reminder for your upcoming interview for '{drive.title}' at {company_name} scheduled at {app.interview_time}. Meeting Link: {app.interview_link or 'Will be shared soon'}\n")
            f.write(f"[GCHAT] Space: GChat Room | Message: 🔔 Interview Reminder for {student.name}: {drive.title} with {company_name} is scheduled on {app.interview_time}. Link: {app.interview_link or 'N/A'}\n")
            f.write(f"[SMS]   To: +1-Simulated-SMS | Message: Hi {student.name}, your interview for '{drive.title}' is scheduled on {app.interview_time}. Join via: {app.interview_link or 'N/A'}\n")
            f.write("="*60 + "\n\n")
            
        # save notification in satabase
        notif = Notification(
            user_id=student_user.id,
            message=f"🔔 Interview Reminder: Your interview for '{drive.title}' with {company_name} is scheduled on {app.interview_time}.",
            link=app.interview_link or None
        )
        db.session.add(notif)
        count += 1
        
    if count > 0:
        db.session.commit()
    print(f"Sent {count} interview reminders.")
    return f"Sent {count} reminders."


@shared_task
def monthly_activity_report():
    companies = CompanyProfile.query.filter_by(status='Approved').all()
    os.makedirs('static/reports', exist_ok=True)
    month_year = datetime.now().strftime("%B_%Y")
    report_date = datetime.now().strftime("%B %d, %Y")
    
    count = 0
    for company in companies:
        user = company.user
        if not user:
            continue
            
        drives = PlacementDrive.query.filter_by(company_id=company.id).all()
        drive_ids = [d.id for d in drives]
        
        total_drives = len(drives)
        apps = Application.query.filter(Application.drive_id.in_(drive_ids)).all() if drive_ids else []
        total_apps = len(apps)
        
        applied_count = sum(1 for a in apps if a.status == 'Applied')
        shortlisted_count = sum(1 for a in apps if a.status == 'Shortlisted')
        selected_count = sum(1 for a in apps if a.status == 'Selected')
        rejected_count = sum(1 for a in apps if a.status == 'Rejected')
        
        avg_salary = sum(d.salary for d in drives) / total_drives if total_drives > 0 else 0
        max_salary = max([d.salary for d in drives]) if drives else 0
        
        # HTML report content
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{company.name} Monthly Placement Report - {month_year}</title>
    <style>
        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            margin: 0;
            padding: 40px;
        }}
        .report-card {{
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            max-width: 800px;
            margin: 0 auto;
            overflow: hidden;
            border: 1px solid #e2e8f0;
        }}
        .header {{
            background: linear-gradient(135deg, #0284c7, #0369a1);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 16px;
        }}
        .content {{
            padding: 40px;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .meta-item {{
            background: #f1f5f9;
            padding: 15px 20px;
            border-radius: 8px;
        }}
        .meta-item label {{
            font-size: 11px;
            text-transform: uppercase;
            font-weight: 700;
            color: #64748b;
            display: block;
            margin-bottom: 5px;
        }}
        .meta-item span {{
            font-size: 18px;
            font-weight: 600;
            color: #0f172a;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: #0f172a;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            border: 1px solid #e2e8f0;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }}
        .stat-card.applied {{ border-left: 4px solid #eab308; }}
        .stat-card.shortlisted {{ border-left: 4px solid #06b6d4; }}
        .stat-card.selected {{ border-left: 4px solid #22c55e; }}
        .stat-card.rejected {{ border-left: 4px solid #ef4444; }}
        
        .stat-num {{
            font-size: 24px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 5px;
        }}
        .stat-lbl {{
            font-size: 12px;
            color: #64748b;
            font-weight: 500;
        }}
        .table-container {{
            overflow-x: auto;
            margin-top: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th {{
            background-color: #f1f5f9;
            padding: 12px 15px;
            font-size: 12px;
            font-weight: 600;
            color: #475569;
            border-bottom: 1px solid #e2e8f0;
        }}
        td {{
            padding: 12px 15px;
            font-size: 14px;
            border-bottom: 1px solid #f1f5f9;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 4px;
        }}
        .badge.success {{ background-color: #dcfce7; color: #15803d; }}
        .badge.info {{ background-color: #ecfeff; color: #0891b2; }}
        .badge.warning {{ background-color: #fef9c3; color: #a16207; }}
        .badge.danger {{ background-color: #fee2e2; color: #b91c1c; }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8fafc;
            border-top: 1px solid #e2e8f0;
            font-size: 12px;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <div class="report-card">
        <div class="header">
            <h1>Monthly Placement Report</h1>
            <p>{company.name} &bull; {month_year.replace('_', ' ')}</p>
        </div>
        <div class="content">
            <div class="meta-grid">
                <div class="meta-item">
                    <label>Report Generated</label>
                    <span>{report_date}</span>
                </div>
                <div class="meta-item">
                    <label>Active Placement Drives</label>
                    <span>{total_drives}</span>
                </div>
                <div class="meta-item">
                    <label>Average Salary Package</label>
                    <span>${avg_salary:,.2f}</span>
                </div>
                <div class="meta-item">
                    <label>Highest Salary Offered</label>
                    <span>${max_salary:,.2f}</span>
                </div>
            </div>

            <div class="section-title">Application Funnel Statistics</div>
            <div class="stats-grid">
                <div class="stat-card applied">
                    <div class="stat-num">{applied_count}</div>
                    <div class="stat-lbl">Applied</div>
                </div>
                <div class="stat-card shortlisted">
                    <div class="stat-num">{shortlisted_count}</div>
                    <div class="stat-lbl">Shortlisted</div>
                </div>
                <div class="stat-card selected">
                    <div class="stat-num">{selected_count}</div>
                    <div class="stat-lbl">Selected (Placed)</div>
                </div>
                <div class="stat-card rejected">
                    <div class="stat-num">{rejected_count}</div>
                    <div class="stat-lbl">Rejected</div>
                </div>
            </div>

            <div class="section-title">Placement Drive Details</div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Drive Title</th>
                            <th>Min CGPA</th>
                            <th>Salary Package</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
    """
        
        if drives:
            for drive in drives:
                status_class = "success" if drive.status == 'Approved' else "warning" if drive.status == 'Pending' else "danger" if drive.status == 'Rejected' else "info"
                html_content += f"""
                        <tr>
                            <td><strong>{drive.title}</strong></td>
                            <td>{drive.min_cgpa} CGPA</td>
                            <td>${drive.salary:,.2f}</td>
                            <td><span class="badge {status_class}">{drive.status}</span></td>
                        </tr>
                """
        else:
            html_content += """
                        <tr>
                            <td colspan="4" style="text-align: center; color: #64748b;">No placement drives found.</td>
                        </tr>
            """
            
        html_content += f"""
                    </tbody>
                </table>
            </div>

            <div class="section-title">Selected Candidates & Placements</div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Candidate Name</th>
                            <th>Drive Role</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        selected_apps = [a for a in apps if a.status == 'Selected']
        if selected_apps:
            for app in selected_apps:
                student_name = app.student.name if app.student else "Unknown"
                drive_title = app.drive.title if app.drive else "Unknown"
                html_content += f"""
                        <tr>
                            <td><strong>{student_name}</strong></td>
                            <td>{drive_title}</td>
                            <td><span class="badge success">Placed</span></td>
                        </tr>
                """
        else:
            html_content += """
                        <tr>
                            <td colspan="3" style="text-align: center; color: #64748b;">No candidate placements recorded yet.</td>
                        </tr>
            """
            
        html_content += f"""
                    </tbody>
                </table>
            </div>
        </div>
        <div class="footer">
            Placement Portal &bull; Generated via automated Celery Beat Job.
        </div>
    </div>
</body>
</html>
"""
        filename = f"static/reports/company_{company.id}_report_{month_year}.html"
        with open(filename, "w", encoding="utf-8") as rf:
            rf.write(html_content)
            
        # Create user notification for company
        notif = Notification(
            user_id=user.id,
            message=f"📊 Your monthly placement performance report for {month_year.replace('_', ' ')} is now ready for view.",
            link=f"/api/reports/company_{company.id}_report_{month_year}.html"
        )
        db.session.add(notif)
        count += 1
        
    if count > 0:
        db.session.commit()
    print(f"Generated monthly reports for {count} companies.")
    return f"Generated {count} reports."
