#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run database initialization/migrations
# We can't easily run the python script here if it needs a full app context and DB access
# but we can try. If it fails, the deploy will fail early which is better.
# python -c "from app import create_app, init_db; app=create_app(); init_db(app)"
