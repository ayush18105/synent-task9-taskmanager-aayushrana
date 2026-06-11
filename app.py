from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import csv

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# User Model
# =========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


# =========================
# Task Model
# =========================
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    priority = db.Column(db.String(20))
    due_date = db.Column(db.String(50))
    status = db.Column(db.String(20), default="Pending")
    user_id = db.Column(db.Integer)


# =========================
# Create Database
# =========================
with app.app_context():
    db.create_all()


# =========================
# Home
# =========================
@app.route('/')
def home():
    return redirect('/login')


# =========================
# Register
# =========================
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            flash("Username already exists!")
            return redirect('/register')

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration Successful!")
        return redirect('/login')

    return render_template('register.html')


# =========================
# Login
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session['user_id'] = user.id

            return redirect('/dashboard')

        flash("Invalid Username or Password")

    return render_template('login.html')


# =========================
# Dashboard
# =========================
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    uid = session['user_id']

    if request.method == 'POST':

        title = request.form['title']
        priority = request.form['priority']
        due_date = request.form['due_date']

        task = Task(
            title=title,
            priority=priority,
            due_date=due_date,
            user_id=uid
        )

        db.session.add(task)
        db.session.commit()

    search = request.args.get('search')

    if search:

        tasks = Task.query.filter(
            Task.user_id == uid,
            Task.title.contains(search)
        ).all()

    else:

        tasks = Task.query.filter_by(
            user_id=uid
        ).all()

    total = Task.query.filter_by(
        user_id=uid
    ).count()

    completed = Task.query.filter_by(
        user_id=uid,
        status="Completed"
    ).count()

    pending = Task.query.filter_by(
        user_id=uid,
        status="Pending"
    ).count()

    return render_template(
        'dashboard.html',
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending
    )


# =========================
# Edit Task
# =========================
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):

    if 'user_id' not in session:
        return redirect('/login')

    task = Task.query.get_or_404(id)

    if request.method == 'POST':

        task.title = request.form['title']
        task.priority = request.form['priority']
        task.due_date = request.form['due_date']
        task.status = request.form['status']

        db.session.commit()

        flash("Task Updated Successfully!")

        return redirect('/dashboard')

    return render_template(
        'edit_task.html',
        task=task
    )


# =========================
# Delete Task
# =========================
@app.route('/delete/<int:id>')
def delete(id):

    if 'user_id' not in session:
        return redirect('/login')

    task = Task.query.get_or_404(id)

    db.session.delete(task)
    db.session.commit()

    flash("Task Deleted Successfully!")

    return redirect('/dashboard')


# =========================
# Admin Dashboard
# =========================
@app.route('/admin')
def admin():

    if 'user_id' not in session:
        return redirect('/login')

    total_users = User.query.count()

    total_tasks = Task.query.count()

    completed = Task.query.filter_by(
        status="Completed"
    ).count()

    pending = Task.query.filter_by(
        status="Pending"
    ).count()

    return render_template(
        'admin.html',
        total_users=total_users,
        total_tasks=total_tasks,
        completed=completed,
        pending=pending
    )


# =========================
# Profile
# =========================
@app.route('/profile')
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    user = User.query.get(
        session['user_id']
    )

    return render_template(
        'profile.html',
        user=user
    )


# =========================
# Export CSV
# =========================
@app.route('/export')
def export():

    if 'user_id' not in session:
        return redirect('/login')

    tasks = Task.query.filter_by(
        user_id=session['user_id']
    ).all()

    with open(
        'tasks.csv',
        'w',
        newline=''
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            'Title',
            'Priority',
            'Due Date',
            'Status'
        ])

        for task in tasks:

            writer.writerow([
                task.title,
                task.priority,
                task.due_date,
                task.status
            ])

    return "tasks.csv exported successfully!"


# =========================
# Logout
# =========================
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


# =========================
# Run App
# =========================
if __name__ == '__main__':
    app.run(debug=True)