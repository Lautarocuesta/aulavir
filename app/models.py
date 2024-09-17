from . import db
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    # Puedes agregar más campos según necesites

    def __repr__(self):
        return f"User('{self.username}')"

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    students = db.relationship('User', backref='enrolled_courses')

class User(UserMixin):
    def __init__(self, id):
        self.id = id