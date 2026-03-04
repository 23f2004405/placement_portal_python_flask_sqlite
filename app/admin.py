from flask import Blueprint,request
from app import db 
from flask import render_template,flash,redirect,url_for,abort
from app.forms import login_form
from app.model import UserRole,User,Company,ApprovalStatus,PlacementDrive,DriveStatus,Application,Student,ApplicationStatus
from flask_login import current_user, login_user,login_required
import sqlalchemy as sa

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def check_admin():
    if current_user.role!=UserRole.ADMIN:
        flash('not a valid admin user')
        return redirect(url_for('main.landing_page'))
    return None

@admin_bp.route('/login',methods=['GET','POST'])
def admin_login():
    form=login_form()
    if form.validate_on_submit():
        user=db.session.scalar(sa.select(User).where(User.username==form.username.data,User.role==UserRole.ADMIN))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('admin.admin_login'))
        login_user(user,remember=False)
           
        flash('Logged in as Admin')
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin/login.html',form=form)

@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    check = check_admin()
    if check:
        return check
    total_students = db.session.scalar(sa.select(sa.func.count()).select_from(User).where(User.role == UserRole.STUDENT,User.is_blacklisted == False))
    total_approved_companies = db.session.scalar(sa.select(sa.func.count()).select_from(User).join(Company).where(User.role==UserRole.COMPANY,User.is_blacklisted==False,Company.approval_status==ApprovalStatus.APPROVED))
    total_pending_companies =  db.session.scalar(sa.select(sa.func.count()).select_from(User).join(Company).where(User.role==UserRole.COMPANY,User.is_blacklisted==False,Company.approval_status==ApprovalStatus.PENDING))
    total_applications = db.session.scalar(sa.select(sa.func.count()).select_from(Application))
    total_pending_drives = db.session.scalar(sa.select(sa.func.count()).select_from(PlacementDrive).where(PlacementDrive.status==DriveStatus.PENDING))
    total_approved_drives = db.session.scalar(sa.select(sa.func.count()).select_from(PlacementDrive).where(PlacementDrive.status==DriveStatus.APPROVED))
    total_closed_drives = db.session.scalar(sa.select(sa.func.count()).select_from(PlacementDrive).where(PlacementDrive.status==DriveStatus.CLOSED))

    return render_template('admin/dashboard.html',total_students=total_students,total_approved_companies=total_approved_companies,total_pending_companies=total_pending_companies,total_applications=total_applications,total_pending_drives=total_pending_drives,total_approved_drives=total_approved_drives,total_closed_drives=total_closed_drives)

@admin_bp.route('/company_registration_applications')
@login_required
def company_registration_applications():
    check = check_admin()
    if check:
        return check
    registration_applications = db.session.scalars(sa.select(User).join(Company).where(Company.approval_status==ApprovalStatus.PENDING,User.role==UserRole.COMPANY)).all()
    return render_template('admin/company_registration_applications.html',registration_applications=registration_applications)

@admin_bp.route('/view_registration_details/<user_id>')
@login_required
def view_registration_details(user_id):
    check = check_admin()
    if check:
        return check
    company_user = db.session.scalar(sa.select(User).where(User.id==user_id))
    return render_template('admin/view_registration_details.html',company_user=company_user)

@admin_bp.route('/approve_company_registration/<user_id>',methods=['POST'])
@login_required
def approve_company_registration(user_id):
    check = check_admin()
    if check:
        return check
    company = db.session.scalar(sa.select(Company).where(Company.user_id == user_id))
    if not company:
        abort(404)
    company.approval_status = ApprovalStatus.APPROVED
    try:
        db.session.commit()
        flash('Company Approved.')
    except:
        db.session.rollback()
        abort(400)
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/reject_company_registration/<user_id>',methods=['POST'])
@login_required
def reject_company_registration(user_id):
    check = check_admin()
    if check:
        return check
    company = db.session.scalar(sa.select(Company).where(Company.user_id == user_id))
    if not company:
        abort(404)
    company.approval_status = ApprovalStatus.REJECTED
    try:
        db.session.commit()
        flash('Company Approval Rejected.')
    except:
        db.session.rollback()
        abort(400)
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/placement_drives')
@login_required
def view_placement_drives():
    check = check_admin()
    if check:
        return check
    company_name = request.args.get('company_name')
    company_username = request.args.get('company_username')
    drive_id = request.args.get('drive_id')
    status = request.args.get('status')

    query = (sa.select(PlacementDrive).join(Company).join(User))

    if drive_id:
        query = query.where(PlacementDrive.id == drive_id)
    if company_name:
        query = query.where(Company.company_name.ilike(f"%{company_name}%"))
    if company_username:
        query = query.where(User.username.ilike(f"%{company_username}%"))
    if status:
        query = query.where(PlacementDrive.status == DriveStatus[status])
       
    placement_drives = db.session.scalars(query).all()

    return render_template('admin/placement_drives.html',placement_drives=placement_drives)

@admin_bp.route('/view_drive_details/<drive_id>')
@login_required
def view_drive_details(drive_id):
    check = check_admin()
    if check:
        return check
    drive = db.session.get(PlacementDrive,drive_id)
    return render_template('admin/view_drive_details.html',drive=drive)

@admin_bp.route('/cancel_drive/<drive_id>',methods=['POST'])
@login_required
def cancel_drive(drive_id):
    check = check_admin()
    if check:
        return check
    drive = db.session.get(PlacementDrive,drive_id)
    if not drive:
        abort(404)
    drive.status=DriveStatus.CANCELLED
    try:
        db.session.commit()
    except:
        db.session.rollback()
        abort(400)
    flash('Drive cancelled')
    return redirect(url_for('admin.view_placement_drives'))
    
@admin_bp.route('/approve_drive/<drive_id>',methods=['POST'])
@login_required
def approve_drive(drive_id):
    check = check_admin()
    if check:
        return check
    drive = db.session.get(PlacementDrive,drive_id)
    drive.status=DriveStatus.APPROVED
    if not drive:
        abort(404)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        abort(400)
    flash('Drive Approved')
    return redirect(url_for('admin.view_placement_drives'))

@admin_bp.route('/view_applications/<drive_id>')
@login_required
def view_applications(drive_id):
    check = check_admin()
    if check:
        return check
    drive = db.session.get(PlacementDrive,drive_id)
    drive_student_applications = drive.applications
    return render_template('admin/view_applications.html',drive_student_applications=drive_student_applications)

@admin_bp.route('/view_company')
@login_required
def view_company():
    check =  check_admin()
    if check:
        return check
    username = request.args.get('username')
    name =  request.args.get('name')
    company_id = request.args.get('company_id')
    query = sa.select(User).join(Company).where(User.role == UserRole.COMPANY)
    
    if name:
        query = query.where(User.name.ilike(f"%{name}%"))
    if username:
        query = query.where(User.username==username)
    if company_id:
        query = query.where(Company.id==int(company_id))

    companies = db.session.scalars(query).all()

    return render_template('admin/view_company.html',companies=companies)

@admin_bp.route('/view_company_details/<user_id>')
@login_required
def view_company_details(user_id):
    check =  check_admin()
    if check:
        return check
    user = db.session.scalar(sa.select(User).where(User.role == UserRole.COMPANY,User.id==user_id))
    return render_template('admin/view_company_details.html',user=user)

@admin_bp.route('/blacklist_user/<user_id>',methods=['POST'])
@login_required
def blacklist_user(user_id):
    check =  check_admin()
    if check:
        return check
    user = db.session.get(User,user_id)
    if not user:
        abort(404)
    user.is_blacklisted = True
    try:
        db.session.commit()
    except:
        db.session.rollback()
        abort(400)
    flash('User Blacklisted')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/remove_blacklist/<user_id>',methods=['POST'])
@login_required
def remove_blacklist(user_id):
    check =  check_admin()
    if check:
        return check
    user = db.session.get(User,user_id)
    if not user:
        abort(404)
    user.is_blacklisted = False
    try:
        db.session.commit()
    except:
        db.session.rollback()
        abort(400)
    flash('User Removed from Blacklist')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/view_student')
@login_required
def view_student():
    check = check_admin()
    if check:
        return check

    username = request.args.get('username')
    name = request.args.get('name')
    roll_number = request.args.get('roll_number')

    query = sa.select(User).join(Student).where(User.role == UserRole.STUDENT)

    if name:
        query = query.where(User.name.ilike(f"%{name}%"))

    if username:
        query = query.where(User.username == username)

    if roll_number:
        query = query.where(Student.roll_number == roll_number)

    students = db.session.scalars(query).all()

    return render_template('admin/view_student.html', students=students)

@admin_bp.route('/view_student_details/<int:user_id>')
@login_required
def view_student_details(user_id):
    check = check_admin()
    if check:
        return check
    user = db.session.scalar(sa.select(User).join(Student).where(User.role == UserRole.STUDENT,User.id == user_id))
    return render_template('admin/view_student_details.html', user=user)
