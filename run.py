from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Esto creará las tablas en la base de datos si no existen
    app.run(debug=True)