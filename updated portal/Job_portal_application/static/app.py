from flask import Flask, render_template, session, redirect, url_for, flash, request
from werkzeug.utils import secure_filename
from forms import SignupForm, LoginForm, JobApplicationForm
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from forms import ResumeForm
import os
from forms import JobPostForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this_is_mysecrete_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Initialize the database
db = SQLAlchemy(app)

# user model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    gender = db.Column(db.String(20))
    dob = db.Column(db.String(50))
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="jobseeker")
    is_admin = db.Column(db.Boolean, default=False)  
    
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    job_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    
    def __repr__(self):
        return f'<User {self.username}>'


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", title="Home")


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
    jobs = Job.query.all()
    return render_template("jobs.html", jobs=jobs)


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


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))


@app.route('/admin')
def admin_dashboard():
    if not session.get('user_id') or not session.get('role') == 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('login'))

    users = Users.query.all()
    resumes = os.listdir(os.path.join('static', 'resumes'))
    return render_template("admin_dashboard.html", users=users, resumes=resumes)



@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if not session.get('role') == 'admin':
        flash("Unauthorized", "danger")
        return redirect(url_for('login'))

    user = Users.query.get_or_404(user_id)
    if user.email == 'admin@jobnest.com':
        flash("Cannot delete default admin", "warning")
        return redirect(url_for('admin_dashboard'))

    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully", "success")
    return redirect(url_for('admin_dashboard'))


@app.route("/view_resume/<filename>")
def view_resume(filename):
    if not session.get('role') == 'admin' and session.get('role') != 'recruiter':
        flash("Unauthorized", "danger")
        return redirect(url_for("login"))

    path = os.path.join("static", "resumes", filename)
    if not os.path.exists(path) or not filename.endswith(".txt"):
        flash("Resume not found or not viewable.", "warning")
        return redirect(url_for("admin_dashboard"))

    with open(path, "r", encoding="utf-8") as file:
        content = file.read()

    return render_template("resume_viewer.html", content=content, filename=filename)


@app.route("/delete_resume/<filename>")
def delete_resume(filename):
    if not session.get('role') == 'admin':
        flash("Unauthorized", "danger")
        return redirect(url_for("login"))

    path = os.path.join("static", "resumes", filename)
    if os.path.exists(path):
        os.remove(path)
        flash(f"{filename} deleted successfully.", "success")
    else:
        flash("File not found.", "warning")

    return redirect(url_for("admin_dashboard"))


@app.route("/post_job", methods=["GET", "POST"])
def post_job():
    if session.get("role") != "admin":
        flash("Only admins can post jobs.", "danger")
        return redirect(url_for("home"))

    form = JobPostForm()
    if form.validate_on_submit():
        new_job = Job(
            title=form.title.data,
            company=form.company.data,
            location=form.location.data,
            job_type=form.job_type.data,
            description=form.description.data
        )
        db.session.add(new_job)
        db.session.commit()
        flash("Job posted successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("post_job.html", form=form)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        
        if not Users.query.filter_by(email='admin@jobnest.com').first():
            from werkzeug.security import generate_password_hash
            admin_user = Users(
             username='admin',
                email='admin@jobnest.com',
                password=generate_password_hash('admin123'),
                role='admin',
                 is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()

    app.run(debug=True)
