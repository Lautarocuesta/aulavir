import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email
from wtforms.validators import DataRequired, EqualTo, ValidationError
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads/'  # Carpeta para almacenar los archivos subidos
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

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

class Maestro(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f"Maestro('{self.username}')"

        
materias_enlistadas = db.Table('materias_enlistadas',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
)

class Course(db.Model):
    __tablename__ = 'course' 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Asegúrate de que el instructor sea obligatorio
    instructor = db.relationship('User', backref='courses_taught')  # Relación con el instructor
    estudiantes = db.relationship('User', secondary=materias_enlistadas, backref='courses')  # Relación con los estudiantes

    def __repr__(self):
        return f"<Course(name={self.name}, instructor_id={self.instructor_id})>"


class SignUpForm(FlaskForm):
    is_teacher=BooleanField('maestro o estudiante?')
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class addclassForm(FlaskForm):
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
    # Verificar que el usuario sea un instructor
    if current_user.role != 'instructor':
        flash('Acceso denegado: Solo los instructores pueden agregar cursos.', 'danger')
        return redirect(url_for('dashboard'))

    form = addclassForm()
    
    if form.validate_on_submit():
        # Crear un nuevo curso
        new_course = Course(name=form.course_name.data, instructor_id=current_user.id)
        
        try:
            db.session.add(new_course)
            db.session.commit()
            flash('Curso agregado exitosamente.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()  # Deshacer cambios en caso de error
            flash('Error al agregar el curso: ' + str(e), 'danger')

    return render_template('add_course.html', form=form)

# Verificar si el archivo tiene una extensión permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Comprobar si el archivo ha sido subido
        if 'file' not in request.files:
            flash('No se ha seleccionado ningún archivo.')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Si el archivo es válido, guardarlo
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('Archivo subido exitosamente.')
            return redirect(url_for('upload_file'))
    
    return render_template('upload.html')




@app.route('/añadir_estudiante/<int:curso_id>', methods=['POST'])
@login_required
def añadir_estudiante(curso_id):
    course = Course.query.get_or_404(curso_id)
    
    # Verificar si el usuario actual es el instructor del curso
    if current_user.id != course.instructor_id:
        flash('Acceso denegado: Solo el instructor puede añadir estudiantes.', 'danger')
        return redirect(url_for('dashboard'))

    student_id = request.form.get('student_id')  # Obtener el ID del estudiante desde el formulario

    student = User.query.get(student_id)
    if student:
        if student not in course.estudiantes:  # Verificar si el estudiante ya está en el curso
            course.estudiantes.append(student)  # Añadir el estudiante al curso
            db.session.commit()
            flash('Estudiante añadido al curso exitosamente.', 'success')
        else:
            flash('El estudiante ya está inscrito en este curso.', 'warning')
    else:
        flash('Estudiante no encontrado.', 'danger')

    return redirect(url_for('dashboard'))  # Redirigir después de añadir el estudiante






@app.route('/remover_estudiante_de_curso/<int:course_id>/<int:student_id>', methods=['POST'])
@login_required
def remover_estudiante(course_id, student_id):
    course = Course.query.get_or_404(course_id)

    # Verificar si el usuario actual es el instructor del curso
    if current_user.id != course.instructor_id:
        flash('Acceso denegado: Solo el instructor puede remover estudiantes.', 'danger')
        return redirect(url_for('dashboard'))

    student = User.query.get(student_id)
    if student in course.estudiantes:
        course.estudiantes.remove(student)  # Remover el estudiante del curso
        db.session.commit()
        flash('Estudiante removido del curso exitosamente.', 'success')
    else:
        flash('El estudiante no está inscrito en este curso.', 'warning')

    return redirect(url_for('dashboard'))  # Redirigir después de remover el estudiante


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(debug=True)
