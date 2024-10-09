import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user


# Configuración de la aplicación
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'patri'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://uamws7gyeh4cvtip:Oeco6Lr2lb2XEppKt2gV@bz0veppeu5g5enzhkrdq-mysql.services.clever-cloud.com:3306/bz0veppeu5g5enzhkrdq?ssl_disabled=True'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# Inicialización de Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
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
    db.Column('curso_id', db.Integer, db.ForeignKey('curso.id'), primary_key=True)
)

class Curso(db.Model):
    __tablename__ = 'curso'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    instructor = db.relationship('User', backref='cursos_taught')
    estudiantes = db.relationship('User', secondary=materias_enlistadas, backref='courses')

    def __repr__(self):
        return f"<Curso(name={self.name}, instructor_id={self.instructor_id})>"
    
class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_curso = db.Column(db.String(100))
    archivo = db.Column(db.String(100))  # Almacena el nombre del archivo
    tipo_tarea = db.Column(db.String(100))  # 'tarea' o 'examen'
    
    def __repr__(self):
        return f'<Tarea {self.nombre_curso}>'

class Evaluacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    descripcion = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Evaluacion {self.nombre}>'

# Inicialización de Flask-Admin
admin = Admin(app, name='Aula Virtual', template_mode='bootstrap3')
admin.add_view(ModelView(Evaluacion, db.session))

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'start': self.start.isoformat(),
            'end': self.end.isoformat()
        }

# Formularios
class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('user', 'User')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AddClassForm(FlaskForm):
    course_name = StringField('Nombre del Curso', validators=[DataRequired()])
    submit = SubmitField('Agregar Curso')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rutas
@app.route('/')
def index():
    return render_template('index.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login exitoso. ¡Bienvenido!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login fallido. Revisa tu nombre de usuario y contraseña.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    form = SignUpForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        
        new_user = User(username=form.username.data, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Tu cuenta ha sido creada exitosamente. ¡Ahora puedes iniciar sesión!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la cuenta: {str(e)}', 'danger')

    return render_template('sign_in.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    courses = Curso.query.all()
    return render_template('dashboard.html', courses=courses)

@app.route('/courses')
def courses():
    return render_template('courses.html')
@app.route('/profile')
def profile():
    return render_template('profile.html')



@app.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if current_user.role != 'instructor':
        flash('Acceso denegado: Solo los instructores pueden agregar cursos.', 'danger')
        return redirect(url_for('dashboard'))

    form = AddClassForm()
    
    if form.validate_on_submit():
        new_course = Curso(name=form.course_name.data, instructor_id=current_user.id)
        try:
            db.session.add(new_course)
            db.session.commit()
            flash('Curso agregado exitosamente.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error al agregar el curso: ' + str(e), 'danger')

    return render_template('add_course.html', form=form)

# Verificar si el archivo tiene una extensión permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se ha seleccionado ningún archivo.')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('Archivo subido exitosamente.')
            return redirect(url_for('upload_file'))
    
    return render_template('upload.html')

@app.route('/añadir_estudiante/<int:curso_id>', methods=['POST'])
@login_required
def añadir_estudiante(curso_id):
    course = Curso.query.get_or_404(curso_id)

    if current_user.id != course.instructor_id:
        flash('Acceso denegado: Solo el instructor puede añadir estudiantes.', 'danger')
        return redirect(url_for('dashboard'))  

    student_id = request.form.get('student_id')
    student = User.query.get(student_id)
    if student:
        if student not in course.estudiantes:
            course.estudiantes.append(student)
            db.session.commit()
            flash('Estudiante añadido al curso exitosamente.', 'success')
        else:
            flash('El estudiante ya está inscrito en este curso.', 'warning')
    else:
        flash('Estudiante no encontrado.', 'danger')

    return redirect(url_for('dashboard'))

@app.route('/remover_estudiante_de_curso/<int:curso_id>/<int:student_id>', methods=['POST'])
@login_required
def remover_estudiante(curso_id, student_id):
    course = Curso.query.get_or_404(curso_id)

    if current_user.id != course.instructor_id:
        flash('Acceso denegado: Solo el instructor puede remover estudiantes.', 'danger')
        return redirect(url_for('dashboard'))  
    

    student = User.query.get(student_id)

    if student and student in course.estudiantes:
        course.estudiantes.remove(student)
        db.session.commit()
        flash('Estudiante removido del curso exitosamente.', 'success')
    else:
        flash('El estudiante no está inscrito en este curso.', 'danger')

    return redirect(url_for('dashboard'))

# Ruta para las tareas de cada materia
@app.route('/course/<int:course_id>/tasks')
def course_tasks(course_id):
    if course_id == 1:
        return render_template('tareas_artes.html')
    elif course_id == 2:
        return render_template('tareas_economia.html')
    elif course_id == 3:
        return render_template('tareas_educacion_fisica.html')
    elif course_id == 4:
        return render_template('tareas_filosofia.html')
    elif course_id == 5:
        return render_template('tareas_historia.html')
    elif course_id == 6:
        return render_template('tareas_ingles.html')
    elif course_id == 7:
        return render_template('tareas_tecnologia.html')
    elif course_id == 8:
        return render_template('tareas_lengua.html')
    elif course_id == 9:
        return render_template('tareas_matematicas.html')
    elif course_id == 10:
        return render_template('tareas_quimica.html')
    elif course_id == 11:
        return render_template('tareas_fisica.html')
    else:
        return "Curso no encontrado", 404

@app.route('/events')
def get_events():
    """Devuelve todos los eventos en formato JSON."""
    events = Event.query.all()  # Obtener todos los eventos de la base de datos
    return jsonify([event.to_dict() for event in events])  # Convertir los eventos a dict y devolver en JSON

@app.route('/add_event', methods=['POST'])
@login_required
def add_event():
    """Añade un nuevo evento a la base de datos."""
    data = request.get_json()  # Obtener los datos del evento del cuerpo de la solicitud
    try:
        new_event = Event(
            title=data['title'],
            start=datetime.fromisoformat(data['start']),
            end=datetime.fromisoformat(data['end'])
        )
        db.session.add(new_event)  # Añadir el nuevo evento a la sesión
        db.session.commit()  # Guardar los cambios en la base de datos
        return jsonify({'status': 'success', 'message': 'Evento añadido con éxito'})
    except Exception as e:
        db.session.rollback()  # Revertir cambios en caso de error
        return jsonify({'status': 'error', 'message': str(e)}), 400  # Devolver error si falla

@app.route('/tarea/artes')
def tareas_arte():
    return render_template('tareas_artes.html')

@app.route('/tarea/economia')
def tareas_economia():
    return render_template('tareas_economia.html')

@app.route('/tarea/educacion_fisica')
def tareas_educacion_fisica():
    return render_template('tareas_educacion_fisica.html')

@app.route('/tarea/filosofia')
def tareas_filosofia():
    return render_template('tareas_filosofia.html')

@app.route('/tarea/historia')
def tareas_historia():
    return render_template('tareas_historia.html')

@app.route('/tarea/ingles')
def tareas_ingles():
    return render_template('tareas_ingles.html')

@app.route('/tarea/tecnologia')
def tareas_tecnologia():
    return render_template('tareas_tecnologia.html')

@app.route('/tarea/lengua')
def tareas_lengua():
    return render_template('tareas_lengua.html')

@app.route('/tarea/matematicas')
def tareas_matematicas():
    return render_template('tareas_matematicas.html')

@app.route('/tarea/quimica')
def tareas_quimica():
    return render_template('tareas_quimica.html')

@app.route('/tarea/fisica')
def tareas_fisica():
    return render_template('tareas_fisica.html')
@app.route('/tareas/<int:course_id>', methods=['GET'])

def view_tarea(course_id):
    # Lógica para manejar la visualización de tareas
    return render_template('tarea.html', course_id=course_id)


if __name__ == '__main__':
    app.run(debug=True)
