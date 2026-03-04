from flask import Blueprint,session,request,current_app
from app import db 
from flask import render_template,flash,redirect,url_for,abort
from app.forms import register_student_form,login_form,edit_student_profile_form,resume_upload_form
from app.model import UserRole,User,PlacementDrive,DriveStatus,Application,Student,ApplicationStatus
from flask_login import current_user, login_user,logout_user,login_required
import sqlalchemy as sa
from datetime import date
from werkzeug.utils import secure_filename
import uuid
import os


student_bp = Blueprint('student', __name__, url_prefix='/student')

def check_student():
    if current_user.role != UserRole.STUDENT:
        flash('User is not a Student')
        return redirect(url_for('main.landing_page'))
    if current_user.is_blacklisted==True:
        flash('User has been blacklisted')
        return redirect(url_for('main.logout'))
    return None

@student_bp.route('/student_register',methods=['GET','POST'])
def register_student():
    form=register_student_form()
    if form.validate_on_submit():
        user=db.session.scalar(sa.select(User).where(User.username==form.username.data))
        if user:
            flash('User already exists')
            return redirect(url_for('student.student_login'))
        roll_number=db.session.scalar(sa.select(Student).where(Student.roll_number==form.roll_number.data))
        if roll_number:
            flash('Roll Number Already exists')
            return redirect(url_for('student.student_login'))
        user=User(username=form.username.data,name=form.name.data,role=UserRole.STUDENT)
        user.set_password(form.password.data)
        db.session.add(user)

        student=Student(user=user,roll_number=form.roll_number.data,department=form.department.data,cgpa=form.cgpa.data,graduation_year=form.graduation_year.data)

        db.session.add(student)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            abort(400)
        flash('Student created')
        login_user(user,remember=False)

        return redirect(url_for('student.student_dashboard'))

    return render_template('student/register.html',form=form)

@student_bp.route('/student_login',methods=['GET','POST'])
def student_login():
    form=login_form()
    if form.validate_on_submit():
        user=db.session.scalar(sa.select(User).where(User.username==form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('student.student_login'))
        if user.role== UserRole.STUDENT:
            login_user(user,remember=False)
              
            flash('user logged in')
            return redirect(url_for('student.student_dashboard'))
        else:
            flash('This is not a student user')
            return redirect(url_for('student.student_login'))
    return render_template('student/login.html',form=form)

@student_bp.route('/student_dashboard')
@login_required
def student_dashboard():
    check = check_student()
    if check:
        return check
    student=db.session.scalar(sa.select(User).where(User.id==current_user.id))
    return render_template('student/dashboard.html',student=student)

@student_bp.route('/view_placement_drives')
@login_required
def view_placement_drives():
    check = check_student()
    if check:
        return check
    today=date.today()
    current_drives = db.session.scalars(sa.select(PlacementDrive).where(PlacementDrive.status == DriveStatus.APPROVED,PlacementDrive.application_deadline >= today,~PlacementDrive.applications.any(Application.student_id == current_user.student.id))).all()

    return render_template('student/view_placement_drives.html',current_drives=current_drives)

@student_bp.route('/apply_for_drives/<drive_id>',methods=['POST'])
@login_required
def apply_for_drives(drive_id):
    check = check_student()
    if check:
        return check
    drive=db.session.get(PlacementDrive,drive_id)
    if not drive:
        flash('Drive does not exist')
        return redirect(url_for('student.view_placement_drives'))
    today=date.today()
    if drive.application_deadline>=today:
        application= Application(student=current_user.student,drive=drive)
        db.session.add(application)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            abort(400)
        flash('Application Successful')
        return redirect(url_for('student.view_placement_drives'))
    else:
        flash('Deadline passed')
        return redirect(url_for('student.student_dashboard'))

@student_bp.route('/drive_history', methods=['GET'])
@login_required
def drive_history():
    check = check_student()
    if check:
        return check

    drive_status = request.args.get("drive_status")
    app_status = request.args.get("app_status")

    query = (sa.select(Application).join(Application.drive).where(Application.student_id == current_user.student.id))

    if drive_status:
        query = query.where(PlacementDrive.status == DriveStatus[drive_status])
    if app_status:
        query = query.where(Application.status == ApplicationStatus[app_status])

    applications = db.session.scalars(query).all()

    return render_template("student/drive_history.html",applications=applications,selected_drive_status=drive_status,selected_app_status=app_status)

@student_bp.route('/edit_student_profile',methods=['GET','POST'])
@login_required
def edit_student_profile():
    check = check_student()
    if check:
        return check
    student=db.session.scalar(sa.select(Student).where(Student.id==current_user.student.id))
    form=edit_student_profile_form(obj=student)
    form.submit.label.text = "Update"
    if form.validate_on_submit():
        form.populate_obj(student)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            abort(400)
        flash("Profile updated successfully")
        return redirect(url_for('student.student_dashboard'))
    
    return render_template('student/edit_student_profile.html', form=form)

@student_bp.route('/view_drive_details/<drive_id>')
@login_required
def view_drive_details(drive_id):
    check = check_student()
    if check:
        return check
    drive=db.session.get(PlacementDrive,drive_id)
    application = db.session.scalar(sa.select(Application).where(Application.drive_id == drive_id,Application.student_id == current_user.student.id))
    return render_template('student/view_drive_details.html',drive=drive,application=application)


@student_bp.route('/upload_resume', methods=['GET', 'POST'])
@login_required
def upload_resume():
    form = resume_upload_form()

    if form.validate_on_submit():
        file = form.resume.data
        filename = secure_filename(file.filename)

        unique_name = f"{uuid.uuid4()}_{filename}"

        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)

        file.save(filepath)

        student = current_user.student
        student.resume = f"resumes/{unique_name}"

        db.session.commit()

        flash("Resume uploaded successfully!", "success")
        return redirect(url_for('student.student_dashboard'))

    return render_template("student/upload_resume.html", form=form)