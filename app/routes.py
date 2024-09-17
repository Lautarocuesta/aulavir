from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
# Importa otros módulos necesarios como formularios, modelos, etc.

main = Blueprint('main', __name__)

# Define aquí las rutas de tu aplicación

@main.route('/')
def index():
    return render_template('index.html')

# Otras rutas para login, registro, cursos, etc.
