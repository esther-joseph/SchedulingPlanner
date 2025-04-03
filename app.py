from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import secrets

# Initialize Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schedule.db'  # Database configuration
app.config['SECRET_KEY'] = 'your_secret_key'  # Secret key for session security

db = SQLAlchemy(app)  # Initialize SQLAlchemy for database management

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect unauthorized users to login page

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)  # Token for password reset

# Task model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Load user for session management
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route, displays tasks
@app.route('/')
@login_required
def index():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.date).all()
    return render_template('index.html', tasks=tasks)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Logout route
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# Password reset request route
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            user.reset_token = secrets.token_hex(16)  # Generate a unique reset token
            db.session.commit()
            flash(f'Your reset token: {user.reset_token}', 'info')
        else:
            flash('User not found', 'danger')
    return render_template('reset_password.html')

# Password update route using token
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def update_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        user.password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        user.reset_token = None  # Clear reset token after use
        db.session.commit()
        flash('Password updated successfully', 'success')
        return redirect(url_for('login'))
    return render_template('update_password.html')

# Route to add a new task
@app.route('/add', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('title')
    date = request.form.get('date')
    new_task = Task(title=title, date=datetime.strptime(date, '%Y-%m-%dT%H:%M'), user_id=current_user.id)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))

# Route to delete a task
@app.route('/delete/<int:id>')
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return redirect(url_for('index'))
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

# API Endpoint: Get all tasks for the logged-in user
@app.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.date).all()
    return jsonify([{'id': task.id, 'title': task.title, 'date': task.date.strftime('%Y-%m-%d %H:%M')} for task in tasks])

# API Endpoint: Create a new task
@app.route('/api/task', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()
    new_task = Task(title=data['title'], date=datetime.strptime(data['date'], '%Y-%m-%dT%H:%M'), user_id=current_user.id)
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message': 'Task created successfully'}), 201

# API Endpoint: Delete a task by ID
@app.route('/api/task/<int:id>', methods=['DELETE'])
@login_required
def api_delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted successfully'})

# Run the Flask app
if __name__ == '__main__':
    db.create_all()  # Ensure database tables are created
    app.run(debug=True)
