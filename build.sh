#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run database migrations if migrations directory exists
if [ -d "database/migrations" ] || [ -d "migrations" ]; then
    export FLASK_APP=wsgi.py
    flask db upgrade || true
fi
