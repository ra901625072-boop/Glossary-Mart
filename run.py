import os
from app import create_app, init_db

app = create_app()

if __name__ == '__main__':
    # Initialize database before running
    init_db(app)
    
    # Get port from environment variable (default to 5000)
    port = int(os.environ.get("PORT", 5000))
    
    print("\n" + "="*50)
    print("Jay Goga Kirana Store Management System")
    print("="*50)
    print(f"Admin Username: {app.config['ADMIN_USERNAME']}")
    print(f"Admin Password: {app.config['ADMIN_PASSWORD']}")
    print(f"Server running on port: {port}")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=port)
