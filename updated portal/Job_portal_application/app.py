from flask import Flask, render_template, session, redirect, url_for, flash, request
from werkzeug.utils import secure_filename
from forms import SignupForm, LoginForm, JobApplicationForm
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from forms import ResumeForm
from dotenv import load_dotenv

import os
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')
app.config["SQLALCHEMY_DATABASE_URI"]= os.getenv('SQLALCHEMY_DATABASE_URI')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False

# Initialize the database
db = SQLAlchemy(app)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    job_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('recruiter.id'), nullable=False)
    applications = db.relationship('JobApplication', backref='job', lazy=True)

class Recruiter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    jobs = db.relationship('Job', backref='recruiter', lazy=True)

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    applicant_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    cover_letter = db.Column(db.Text)
    resume_filename = db.Column(db.String(100))  # Path to uploaded file
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)

        
# user model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    gender = db.Column(db.String(20))
    dob = db.Column(db.String(50))
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="jobseeker")

    def __repr__(self):
        return f'<User {self.username}>'


@app.route("/")
def root():
    return redirect(url_for('splash'))
@app.route("/home")
def home():
    return render_template("home.html", title="Home")
@app.route('/splash')
def splash():
    return render_template('splash.html')




@app.route("/layout")
def layout():
    return render_template("layout.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    
    
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = Users.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['email'] = user.email
            session['role'] = user.role
            flash("Logged in Successfully!", "success")
            
            
            if user.role == 'recruiter':
                return redirect(url_for("recruiter_dashboard"))  # Make sure this route exists
            else:
                return redirect(url_for("jobs"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html", form=form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        existing_email = Users.query.filter_by(email=form.email.data).first()
        existing_username = Users.query.filter_by(username=form.username.data).first()

        if existing_email:
            flash("Email is already registered. Please use a different one.", "danger")
            return render_template("signup.html", form=form)

        if existing_username:
            flash("Username is already taken. Please choose a different one.", "danger")
            return render_template("signup.html", form=form)
        hashed_pw = generate_password_hash(form.password.data)
        user = Users(
            username=form.username.data,
            email=form.email.data,
            gender=form.gender.data,
            dob=form.dob.data.strftime("%Y-%m-%d"),
            role=form.role.data,
            password=hashed_pw
        )
        db.session.add(user)
        db.session.commit()

        flash(f"Successfully Registered {form.username.data}", "success")
        return redirect(url_for("login"))  

    return render_template("signup.html", form=form)


@app.route("/jobs")
def jobs():
    all_jobs = Job.query.all()
    return render_template("jobs.html",jobs=all_jobs)







@app.route("/resume", methods=["GET", "POST"])
def resume():
    if not session.get('user_id'):
        flash("Please log in to apply for a job.", "warning")
        return redirect(url_for("login"))

    if session.get('role') != 'jobseeker':
        flash("Only job seekers can submit resumes.", "danger")
        return redirect(url_for("home"))

    form = ResumeForm()
    if request.method == "POST" and form.validate_on_submit():
        filename = None
        if form.resume_file.data:
            resume_file = form.resume_file.data
            filename = secure_filename(resume_file.filename)
            resume_file.save(os.path.join("static/resumes", filename))
        elif form.resume_text.data.strip():
            filename = f"{session['username']}_resume.txt"
            with open(os.path.join("static/resumes", filename), "w") as f:
                f.write(form.resume_text.data)

        flash("Resume submitted successfully!", "success")
        return redirect(url_for("home"))

    return render_template("resume.html", form=form)


@app.route('/add_job', methods=['GET', 'POST'])
def add_job():
    # ✅ Make sure only recruiters can access this
    if session.get('role') != 'recruiter':
        flash("Only recruiters can add jobs.", "danger")
        return redirect(url_for("login"))

    recruiter_id = session.get('user_id')  # ✅ Safe access

    if request.method == 'POST':
        company = request.form['company']
        location = request.form['location']
        job_type = request.form['job_type']
        description = request.form['message']

        new_job = Job(
            company=company,
            location=location,
            job_type=job_type,
            description=description,
            recruiter_id=recruiter_id  # ✅ Correct usage now
        )

        db.session.add(new_job)
        db.session.commit()
        flash("Job added successfully!", "success")
        return redirect(url_for("jobs"))

    return render_template('job listings.html')

@app.route("/success")
def success():
    return render_template("success.html")
@app.route("/uploadedresumes")
def uploadedresumes():
    if session.get('role') != 'recruiter':
        flash("Access restricted to recruiters.", "danger")
        return redirect(url_for('login'))

    recruiter_id = session.get('user_id')
    recruiter_jobs = Job.query.filter_by(recruiter_id=recruiter_id).all()

    applications = []
    for job in recruiter_jobs:
        for application in job.applications:
            applications.append({
                'job_title': job.job_type,
                'applicant_name': application.applicant_name,
                'email': application.email,
                'resume_filename': application.resume_filename,
                'cover_letter': application.cover_letter
            })

    return render_template("uploadedresumes.html", applications=applications)

@app.route("/dashboard")
def dashboard():
    if session.get('role') != 'recruiter':
        flash("Access restricted to recruiters.", "danger")
        return redirect(url_for('login'))

    recruiter_id = session.get('user_id')

    # Fetch jobs posted by this recruiter
    recruiter_jobs = Job.query.filter_by(recruiter_id=recruiter_id).all()
    job_ids = [job.id for job in recruiter_jobs]

    # Count total applications
    total_applications = JobApplication.query.filter(JobApplication.job_id.in_(job_ids)).count()

    # Count open positions
    open_positions = len(recruiter_jobs)

    # Dummy success rate (you can replace with real logic)
    success_rate = 94

    # Dummy average hiring days (replace with real logic if available)
    avg_days_to_hire = 12

    return render_template(
        "dashboard.html",
        total_applications=total_applications,
        open_positions=open_positions,
        success_rate=success_rate,
        avg_days_to_hire=avg_days_to_hire
    )


@app.route("/recruiter")
def recruiter_dashboard():
    if session.get('role') != 'recruiter':
        flash("Access restricted to recruiters.", "danger")
        return redirect(url_for('login'))

    recruiter_id = session.get('user_id')

    recruiter_jobs = Job.query.filter_by(recruiter_id=recruiter_id).all()

    # Calculate stats
    total_applications = sum(len(job.applications) for job in recruiter_jobs)
    open_positions = len(recruiter_jobs)
    success_rate = 94  # Replace with actual logic if needed
    avg_days_to_hire = 12  # Replace with actual logic if needed

    return render_template(
        "recruiter.html",
        applications=[
            {
                'job_title': job.job_type,
                'applicant_name': app.applicant_name,
                'email': app.email,
                'resume_filename': app.resume_filename,
                'cover_letter': app.cover_letter
            }
            for job in recruiter_jobs for app in job.applications
        ],
        total_applications=total_applications,
        open_positions=open_positions,
        success_rate=success_rate,
        avg_days_to_hire=avg_days_to_hire
    )

    

@app.route("/apply/<int:job_id>", methods=["GET", "POST"])
def apply(job_id):
    form = JobApplicationForm()
    job = Job.query.get_or_404(job_id)

    if form.validate_on_submit():
        application = JobApplication(
            applicant_name=form.name.data,
            email=form.email.data,
           
            cover_letter=form.cover_letter.data,
            job_id=job.id
        )
        db.session.add(application)
        db.session.commit()
        flash("Application submitted successfully!", "success")
        return redirect(url_for("jobs"))

    return render_template("apply.html", form=form, job=job)




@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
