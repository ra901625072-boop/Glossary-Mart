"""
e Grossary - Dual Server Development Launcher
Launches both Backend (Flask :5000) and Frontend (HTTP Server :3000) simultaneously.
Press Ctrl+C to stop both servers cleanly.
"""
import os
import sys
import subprocess
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

def main():
    print("=" * 65)
    print(" 🛒 E GROSSARY — DUAL-SERVER DEVELOPMENT ENVIRONMENT")
    print("=" * 65)
    print(" [1/2] Backend API:  http://127.0.0.1:5000/ (Health Check)")
    print("                     http://127.0.0.1:5000/api/products (REST API)")
    print(" [2/2] Frontend UI:  http://localhost:3000/ (Storefront)")
    print("                     http://localhost:3000/customer/shop.html (Customer Shop)")
    print("                     http://localhost:3000/customer/cart.html (Shopping Bag)")
    print("                     http://localhost:3000/customer/orders.html (Orders & Tracking)")
    print("                     http://localhost:3000/admin/index.html (Admin ERP Dashboard)")
    print("                     http://localhost:3000/admin/pos.html (Admin POS Counter)")
    print("                     http://localhost:3000/auth/login.html (Customer & Admin Login)")
    print("=" * 65)
    print(" Starting servers... Press Ctrl+C at any time to stop both.\n")

    # Start Backend API
    backend_proc = subprocess.Popen(
        [sys.executable, "wsgi.py"],
        cwd=PROJECT_ROOT
    )

    # Start Frontend Server
    frontend_proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", "3000", "--directory", "frontend"],
        cwd=PROJECT_ROOT
    )

    try:
        while True:
            # Check if any process exited unexpectedly
            b_poll = backend_proc.poll()
            f_poll = frontend_proc.poll()
            if b_poll is not None:
                print(f"\n[Backend] Process terminated with code {b_poll}")
                break
            if f_poll is not None:
                print(f"\n[Frontend] Process terminated with code {f_poll}")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping development servers...")
    finally:
        for name, proc in [("Frontend", frontend_proc), ("Backend", backend_proc)]:
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except Exception:
                    proc.kill()
        print("Both servers stopped cleanly. Goodbye!")

if __name__ == "__main__":
    main()
