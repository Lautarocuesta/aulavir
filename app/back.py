from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

# Inicialización de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Cambia esto por una clave secreta real
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Cambia la URI según tu base de datos

# Inicialización de la base de datos
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

# Formularios
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AddCourseForm(FlaskForm):
    course_name = StringField('Nombre del Curso', validators=[DataRequired()])
    submit = SubmitField('Agregar Curso')


# Función user_loader requerida por Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rutas
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/courses')
@login_required
def courses():
    # Aquí puedes agregar lógica para mostrar cursos.
    return render_template('courses.html')

@app.route('/dashboard')
@login_required
def dashboard():
    courses = Course.query.all()  # Obtener todos los cursos
    return render_template('dashboard.html', courses=courses)

@app.route('/profile')
@login_required
def profile():
    # Aquí puedes agregar lógica para mostrar el perfil del usuario.
    return render_template('profile.html')

@app.route('/add_course', methods=['GET', 'POST'])
@login_required  # Asegúrate de que solo los usuarios autenticados puedan agregar cursos
def add_course():
    form = AddCourseForm()
    if form.validate_on_submit():
        new_course = Course(name=form.course_name.data, instructor_id=current_user.id)
        db.session.add(new_course)
        db.session.commit()
        flash('Curso agregado exitosamente.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_course.html', form=form)

# Creación de las tablas y ejecución del servidor
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Esto creará las tablas en la base de datos si no existen
    app.run(debug=True)
