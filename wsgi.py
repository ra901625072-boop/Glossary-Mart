from app import create_app, init_db

app = create_app()

# This is for production/gunicorn
if __name__ != '__main__':
    with app.app_context():
        init_db(app)

if __name__ == '__main__':
    # This is for local development if someone still runs python app.py
    init_db(app)
    app.run(debug=True)
