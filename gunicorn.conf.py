import os

# Render provides the PORT environment variable (default: 10000)
port = os.getenv("PORT", "10000")
bind = f"0.0.0.0:{port}"

# Concurrency & worker configuration
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
threads = int(os.getenv("PYTHON_THREADS", "2"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = 5

# Real-time unbuffered logging to stdout / stderr for Render live tail
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
capture_output = True
enable_stdio_inheritance = True
