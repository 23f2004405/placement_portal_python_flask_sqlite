from flask import Blueprint,request
from app import db 
from flask import render_template,flash,redirect,url_for,abort
from app.forms import register_company_form,login_form,create_drive_form
from app.model import UserRole,User,Company,ApprovalStatus,PlacementDrive,DriveStatus,Application,Student,ApplicationStatus
from flask_login import current_user, login_user,login_required
import sqlalchemy as sa

company_bp = Blueprint('company', __name__, url_prefix='/company')

def company_check(c_user):
    if not c_user.is_company():
        abort(403)

    if not c_user.is_approved_company():
        flash("Your company is not approved yet")
        return redirect(url_for('main.logout'))
    
    if c_user.is_blacklisted:
        flash("User has been blacklisted")
        return redirect(url_for('main.logout'))

    return None

@company_bp.route('/registration',methods=['GET','POST'])
def register_company():
    form=register_company_form()
    if form.validate_on_submit():
        user=db.session.scalar(sa.select(User).where(User.username==form.username.data))
        if user:
            flash('User already exists')
            return redirect(url_for('company.login_company'))
        user=User(username=form.username.data,name=form.name.data,role=UserRole.COMPANY)
    
        user.set_password(form.password.data)
        db.session.add(user)

        company = Company(user=user,company_name=form.name.data,hr_contact=form.hr_contact.data,website=form.website.data,approval_status=ApprovalStatus.PENDING)

        db.session.add(company)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            abort(400)
        flash('Company created')
        login_user(user,remember=False)
        
        return redirect(url_for('company.company_dashboard'))
    
    return render_template('company/register.html',form=form)

@company_bp.route('/login',methods=['GET','POST'])
def login_company():
    form=login_form()
    if form.validate_on_submit():
        user=db.session.scalar(sa.select(User).where(User.username==form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('company.login_company'))
        if user.role== UserRole.COMPANY:
            login_user(user,remember=False)
               
            flash('User logged in')
            return redirect(url_for('company.company_dashboard'))
        else:
            flash('This is not a company user')
            return redirect(url_for('company.login_company'))
    return render_template('company/login.html',form=form)

@company_bp.route('/dashboard')
@login_required
def company_dashboard():
    check = company_check(current_user)
    if check:
        return check
    company_user = db.session.scalar(sa.select(Company).where(Company.user_id==current_user.id))
    return render_template('company/dashboard.html',company_user=company_user)

@company_bp.route('/placement_drives', methods=['GET'])
@login_required
def company_placement_drives():
    check = company_check(current_user)
    if check:
        return check

    status = request.args.get('status')      
    drive_id = request.args.get('drive_id')  

    query = sa.select(PlacementDrive).where(PlacementDrive.company_id == current_user.company.id)

    if status:
       query = query.where(PlacementDrive.status == DriveStatus[status])
       

    if drive_id:
        query = query.where(PlacementDrive.id == int(drive_id))

    drives = db.session.scalars(query).all()

    return render_template('company/placement_drives.html',drives=drives,selected_status=status,drive_id=drive_id)

@company_bp.route('/remove_drive/<drive_id>',methods=['POST'])
@login_required
def remove_drive(drive_id):
    check = company_check(current_user)
    if check:
        return check
    
    drive = db.session.get(PlacementDrive, drive_id)
    if drive.company_id != current_user.company.id:
        abort(403)
    db.session.delete(drive)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        abort(400)
    
    flash('Placement Drive Deleted')
    return redirect(url_for('company.company_dashboard'))

@company_bp.route('/close_drive/<drive_id>',methods=['POST'])
@login_required
def close_drive(drive_id):
    check = company_check(current_user)
    if check:
        return check
    drive = db.session.get(PlacementDrive,drive_id)
    if drive.company_id != current_user.company.id:
        abort(403)
    drive.status= DriveStatus.CLOSED
    try:
        db.session.commit()
    except:
        db.session.rollback()
        abort(400)
    flash('Placement Drive Closed')
    return redirect(url_for('company.company_dashboard'))

@company_bp.route('/edit_drive/<drive_id>',methods=['GET','POST'])
@login_required
def edit_drive(drive_id):
    check = company_check(current_user)
    if check:
        return check
    drive = db.session.get(PlacementDrive,drive_id)
    if drive.company_id != current_user.company.id:
        abort(403)
    if drive.status == DriveStatus.CLOSED or drive.status == DriveStatus.CANCELLED:
        flash("Closed drives cannot be edited")
        return redirect(url_for('company.company_dashboard'))
    form = create_drive_form(obj=drive)
    if form.validate_on_submit():
        form.populate_obj(drive) 
        try:
            db.session.commit()
        except:
            db.session.rollback()
            abort(400)
        flash("Drive updated successfully")
        return redirect(url_for('company.company_placement_drives'))
    
    return render_template('company/edit_drive.html', form=form, drive=drive)


@company_bp.route('/create_drive',methods=['GET','POST'])
@login_required
def create_drive():
    check = company_check(current_user)
    if check:
        return check
    form = create_drive_form()
    if form.validate_on_submit():
        placement_drive =  PlacementDrive(job_title=form.job_title.data,job_description=form.job_description.data,eligibility_criteria=form.eligibility_criteria.data,application_deadline=form.application_deadline.data,company=current_user.company)
        db.session.add(placement_drive)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            abort(400)
        flash('Placement Drive Created')
        return redirect(url_for('company.company_placement_drives'))
    
    return render_template('company/create_drive.html',form=form)

@company_bp.route('/applications/<drive_id>')
@login_required
def student_applications(drive_id):
    check = company_check(current_user)
    if check:
        return check
    
    status=request.args.get('status')
    
    if status=="APPLIED":
        applications=db.session.scalars(sa.select(Application).where(Application.drive_id==drive_id,Application.status==ApplicationStatus.APPLIED)).all()
    elif status=="SHORTLISTED":
        applications=db.session.scalars(sa.select(Application).where(Application.drive_id==drive_id,Application.status==ApplicationStatus.SHORTLISTED)).all()
    elif status=="SELECTED":
        applications=db.session.scalars(sa.select(Application).where(Application.drive_id==drive_id,Application.status==ApplicationStatus.SELECTED)).all()
    elif status=="REJECTED":
        applications=db.session.scalars(sa.select(Application).where(Application.drive_id==drive_id,Application.status==ApplicationStatus.REJECTED)).all()
    elif status=="":
        applications=db.session.scalars(sa.select(Application).where(Application.drive_id==drive_id)).all()
    else:
        applications=db.session.scalars(sa.select(Application).where(Application.drive_id==drive_id)).all()
    
    return render_template('company/student_applications.html',applications=applications,selected_status=status,drive_id=drive_id)

@company_bp.route('/view_applicant/<appl_id>')
@login_required
def view_applicant(appl_id):
    check = company_check(current_user)
    if check:
        return check
    applicant=db.session.scalar(sa.select(Student).join(Application).where(Application.id==appl_id))
    application=db.session.get(Application,appl_id)
    return render_template('company/view_applicant.html',application=application,applicant=applicant)

@company_bp.route('/shortlist_applicant/<appl_id>',methods=['POST'])
@login_required
def shortlist_applicant(appl_id):
    check = company_check(current_user)
    if check:
        return check
    application=db.session.scalar(sa.select(Application).where(Application.id==appl_id))
    application.status=ApplicationStatus.SHORTLISTED
    try:
        db.session.commit()
        flash('Applicant Shortlisted')
    except:
        db.session.rollback()
        abort(400)
    return redirect(url_for('company.student_applications',drive_id=db.session.get(Application, appl_id).drive_id))

@company_bp.route('/reject_applicant/<appl_id>',methods=['POST'])
@login_required
def reject_applicant(appl_id):
    check = company_check(current_user)
    if check:
        return check
    application=db.session.scalar(sa.select(Application).where(Application.id==appl_id))
    application.status=ApplicationStatus.REJECTED
    try:
        db.session.commit()
        flash('Applicant Rejected')
    except:
        db.session.rollback()
        abort(400)
    return redirect(url_for('company.student_applications',drive_id=db.session.get(Application, appl_id).drive_id))

@company_bp.route('/select_applicant/<appl_id>',methods=['POST'])
@login_required
def select_applicant(appl_id):
    check = company_check(current_user)
    if check:
        return check
    application=db.session.scalar(sa.select(Application).where(Application.id==appl_id))
    application.status=ApplicationStatus.SELECTED
    try:
        db.session.commit()
        flash('Applicant Selected')
    except:
        db.session.rollback()
        abort(400)
    return redirect(url_for('company.student_applications',drive_id=db.session.get(Application, appl_id).drive_id))

@company_bp.route('/drive_details/<drive_id>')
@login_required
def drive_details(drive_id):
    check = company_check(current_user)
    if check:
        return check
    drive = db.session.get(PlacementDrive,drive_id)
    number_of_applications=db.session.scalar(sa.select(sa.func.count()).select_from(Application).where(Application.drive_id==drive_id))
    return render_template('company/drive_details.html',drive=drive,number_of_applications=number_of_applications)


    


    