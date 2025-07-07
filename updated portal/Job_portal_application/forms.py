from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, PasswordField, SubmitField, BooleanField, TextAreaField, FileField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional
from flask_wtf.file import FileRequired, FileAllowed
from flask_wtf.file import FileField, FileAllowed

class SignupForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(4, 15)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    gender = SelectField("Gender", choices=["male", "female", "other"], validators=[Optional()])
    dob = DateField("Date of birth", validators=[DataRequired()])
    role = RadioField("Register As", choices=[("jobseeker", "Job Seeker"), ("recruiter", "Recruiter")], default="jobseeker", validators=[DataRequired()])  
    password = PasswordField("Password", validators=[DataRequired(), Length(5, 15)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), Length(5, 15), EqualTo("password")])
    submit = SubmitField("Sign Up")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(5, 15)])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login In")

class JobApplicationForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    cover_letter = TextAreaField("Cover Letter", validators=[DataRequired()])
    submit = SubmitField("Apply")

class ResumeForm(FlaskForm):
    resume_file = FileField("Upload Resume", validators=[FileAllowed(['pdf', 'doc', 'docx'])])
    resume_text = TextAreaField("Or Type Your Resume")
    submit = SubmitField("Submit Resume")