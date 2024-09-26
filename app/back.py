from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email
from wtforms.validators import DataRequired, EqualTo, ValidationError

# Inicialización de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = 'patri'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://uamws7gyeh4cvtip:Oeco6Lr2lb2XEppKt2gV@bz0veppeu5g5enzhkrdq-mysql.services.clever-cloud.com:3306/bz0veppeu5g5enzhkrdq' 


db = SQLAlchemy(app)

# Inicialización de Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'  # Nombre de la ruta para la página de login
login_manager.init_app(app)

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f"User('{self.username}')"

enrollments = db.Table('enrollments',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    students = db.relationship('User', secondary=enrollments, backref='courses')




class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AddCourseForm(FlaskForm):
    course_name = StringField('Nombre del Curso', validators=[DataRequired()])
    submit = SubmitField('Agregar Curso')



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.', 'danger')
    return render_template('login.html', form=form)

    
@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    form = SignUpForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('sign_in.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/courses')
@login_required
def courses():
   
    return render_template('courses.html')

@app.route('/dashboard')
@login_required
def dashboard():
    courses = Course.query.all()  
    return render_template('dashboard.html', courses=courses)

@app.route('/profile')
@login_required
def profile():
    
    return render_template('profile.html')

@app.route('/add_course', methods=['GET', 'POST'])
@login_required 
def add_course():
    form = AddCourseForm()
    if form.validate_on_submit():
        new_course = Course(name=form.course_name.data, instructor_id=current_user.id)
        db.session.add(new_course)
        db.session.commit()
        flash('Curso agregado exitosamente.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_course.html', form=form)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(debug=True)
