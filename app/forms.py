from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField ,TextAreaField,DateField,FloatField,IntegerField
from wtforms.validators import DataRequired,EqualTo,Length,ValidationError
from flask_wtf.file import FileField, FileAllowed, FileRequired

class register_company_form(FlaskForm):
    username=StringField('Username',validators=[DataRequired(),Length(max=20)])
    name= StringField('Company name', validators=[DataRequired(),Length(max=120)])
    hr_contact = TextAreaField('HR contact',validators=[Length(max=100)])
    website = StringField('Website link',validators=[Length(max=150)])
    password = PasswordField('Password', validators=[DataRequired(),Length(min=8,max=255)])
    re_enter_password = PasswordField('Enter Password Again',validators=[EqualTo('password')])
    submit = SubmitField('Sign Up')

class login_form(FlaskForm):
    username= StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class create_drive_form(FlaskForm):
    job_title=StringField('Job Title',validators=[DataRequired()])
    job_description=TextAreaField('Job Description',validators=[DataRequired()])
    eligibility_criteria = TextAreaField('Eligibility Criteria',validators=[DataRequired()])
    application_deadline = DateField('Application Deadline',format="%Y-%m-%d",validators=[DataRequired()])
    submit= SubmitField('Create Drive')

class register_student_form(FlaskForm):
    username=StringField('Username',validators=[DataRequired(),Length(max=20)])
    name= StringField('Name', validators=[DataRequired(),Length(max=120)])
    roll_number=StringField('Roll Number', validators=[DataRequired(),Length(max=50)])
    department=StringField('Department',validators=[DataRequired(),Length(max=100)])
    cgpa=FloatField('CGPA',validators=[DataRequired()])
    graduation_year=IntegerField('Graduation Year',validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(),Length(min=8,max=255)])
    re_enter_password = PasswordField('Enter Password Again',validators=[EqualTo('password')])
    submit = SubmitField('Sign Up')

class edit_student_profile_form(FlaskForm):
    roll_number=StringField('Roll Number', validators=[DataRequired(),Length(max=50)])
    department=StringField('department',validators=[DataRequired(),Length(max=100)])
    cgpa=FloatField('CGPA',validators=[DataRequired()])
    graduation_year=IntegerField('Graduation Year',validators=[DataRequired()])
    submit = SubmitField('Sign In')

class resume_upload_form(FlaskForm):
    resume = FileField("Upload Resume",validators=[FileRequired(),FileAllowed(["pdf"], "PDF files only!")])
    submit = SubmitField("Upload")


    def validate_resume(self, field):
        file = field.data
        file.seek(0, 2) 
        size = file.tell()
        file.seek(0) 

        if size > 500 * 1024:  
            raise ValidationError("File must be less than 500 KB.")



