from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

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

# Función user_loader requerida por Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from . import routes, models
