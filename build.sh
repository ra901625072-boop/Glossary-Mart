#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run database migrations
# This ensures the production DB is always in sync with models
export FLASK_APP=wsgi.py
flask db upgrade
