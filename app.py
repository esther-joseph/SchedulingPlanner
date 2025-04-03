from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schedule.db'
db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@app.route('/')
def index():
    tasks = Task.query.order_by(Task.date).all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    title = request.form.get('title')
    date = request.form.get('date')
    new_task = Task(title=title, date=datetime.strptime(date, '%Y-%m-%dT%H:%M'))
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

# API Endpoints
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.order_by(Task.date).all()
    return jsonify([{'id': task.id, 'title': task.title, 'date': task.date.strftime('%Y-%m-%d %H:%M')} for task in tasks])

@app.route('/api/task', methods=['POST'])
def create_task():
    data = request.get_json()
    new_task = Task(title=data['title'], date=datetime.strptime(data['date'], '%Y-%m-%dT%H:%M'))
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message': 'Task created successfully'}), 201

@app.route('/api/task/<int:id>', methods=['DELETE'])
def api_delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted successfully'})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
