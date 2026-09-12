import os
import sys
from backend import create_app, init_db

# Production entry point for Gunicorn:
#   gunicorn wsgi:app
app = create_app()

try:
    with app.app_context():
        init_db(app)
except Exception as e:
    app.logger.warning(f"Startup DB verification deferred or failed: {e}")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"Starting e Grossary on port {port}...")
    for rule in app.url_map.iter_rules():
        print(f"ROUTE: {rule} -> {rule.endpoint}")
    app.run(host='0.0.0.0', port=port, debug=False)

