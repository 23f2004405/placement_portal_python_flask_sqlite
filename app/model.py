from datetime import datetime
import enum
from werkzeug.security import generate_password_hash, check_password_hash
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db,login
from flask_login import UserMixin

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class UserRole(enum.Enum):
    ADMIN = "admin"
    COMPANY = "company"
    STUDENT = "student"


class ApprovalStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    
class DriveStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ApplicationStatus(enum.Enum):
    APPLIED = "applied"
    SHORTLISTED = "shortlisted"
    SELECTED = "selected"
    REJECTED = "rejected"

class User(db.Model,UserMixin):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True)
    username=sa.Column(sa.String(20),unique=True,nullable=False)
    name = sa.Column(sa.String(120), nullable=False)
    password_hash = sa.Column(sa.String(255), nullable=False)

    role = sa.Column(sa.Enum(UserRole), nullable=False)
    is_blacklisted = sa.Column(sa.Boolean, default=False)

    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

    student = so.relationship(
        "Student", back_populates="user", uselist=False
    )
    company = so.relationship(
        "Company", back_populates="user", uselist=False
    )

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str):
        return check_password_hash(self.password_hash, password)
    
    def is_company(self):
        return self.role == UserRole.COMPANY
    
    def is_approved_company(self):
        return (self.is_company() and self.company is not None and self.company.approval_status == ApprovalStatus.APPROVED)

    def __repr__(self):
        return f"<User id={self.id} role={self.role.value}>"
    

    @property
    def is_active(self):
        return True

class Student(db.Model):
    __tablename__ = "students"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), unique=True)
    roll_number = sa.Column(sa.String(50), unique=True, nullable=False)
    department = sa.Column(sa.String(100))
    cgpa = sa.Column(sa.Float)
    graduation_year = sa.Column(sa.Integer)
    resume = sa.Column(sa.String(255))
    user = so.relationship("User", back_populates="student")
    applications = so.relationship("Application", back_populates="student",cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student roll={self.roll_number}>"

class Company(db.Model):
    __tablename__ = "companies"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(
        sa.Integer, sa.ForeignKey("users.id"), unique=True
    )

    company_name = sa.Column(sa.String(150), nullable=False)
    hr_contact = sa.Column(sa.String(100))
    website = sa.Column(sa.String(150))
    
    approval_status = sa.Column(
        sa.Enum(ApprovalStatus),
        default=ApprovalStatus.PENDING
    )

    user = so.relationship("User", back_populates="company")
    drives = so.relationship(
        "PlacementDrive", back_populates="company",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Company {self.company_name}>"

class PlacementDrive(db.Model):
    __tablename__ = "placement_drives"

    id = sa.Column(sa.Integer, primary_key=True)
    company_id = sa.Column(sa.Integer, sa.ForeignKey("companies.id"), nullable=False)
    job_title = sa.Column(sa.String(150), nullable=False)
    job_description = sa.Column(sa.Text)
    eligibility_criteria = sa.Column(sa.Text)

    application_deadline = sa.Column(sa.Date)
    status = sa.Column(sa.Enum(DriveStatus),default=DriveStatus.PENDING)

    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

    company = so.relationship("Company", back_populates="drives")
    applications = so.relationship("Application", back_populates="drive",cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Drive {self.job_title}>"

class Application(db.Model):
    __tablename__ = "applications"

    id = sa.Column(sa.Integer, primary_key=True)
    student_id = sa.Column(sa.Integer, sa.ForeignKey("students.id"), nullable=False)
    drive_id = sa.Column(sa.Integer, sa.ForeignKey("placement_drives.id"), nullable=False)
    applied_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    status = sa.Column(sa.Enum(ApplicationStatus),default=ApplicationStatus.APPLIED)
    student = so.relationship("Student", back_populates="applications")
    drive = so.relationship("PlacementDrive", back_populates="applications")

    __table_args__ = (sa.UniqueConstraint("student_id", "drive_id",name="uq_student_drive"),)

    def __repr__(self):
        return f"<Application s={self.student_id} d={self.drive_id}>" 
    
def create_db_and_seed():
    db.create_all()

    admin = db.session.scalar(sa.select(User).where(User.role == UserRole.ADMIN))

    if admin is None:
        admin = User(username="admin",name="Super Admin",role=UserRole.ADMIN)
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
