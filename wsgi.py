from app import app, init_db

# This is for production/gunicorn
# Note: Database initialization now happens inside app/__init__.py 
# to support both 'gunicorn app:app' and 'gunicorn wsgi:app'

if __name__ == '__main__':
    # This is for local development if someone still runs python wsgi.py
    with app.app_context():
        init_db(app)
    app.run(debug=True)
