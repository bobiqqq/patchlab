from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        # Сохраняет пароль только как hash.
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Сравнивает введённый пароль с сохранённым hash.
        return check_password_hash(self.password_hash, password)


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(20))
    category = db.Column(db.String(50))
    weight = db.Column(db.Integer, default=100)
    source_path = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)


class Patch(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    filename = db.Column(db.String(255))
    file_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='uploaded')
    score = db.Column(db.Integer, default=0)
    checker_output = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('patches', lazy=True))
    task = db.relationship('Task', backref=db.backref('patches', lazy=True))
