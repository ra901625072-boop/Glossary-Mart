@echo off
title e Grossary - Backend API (Port 5000)
echo ============================================================
echo Starting e Grossary Flask API Backend on port 5000...
echo Health check: http://127.0.0.1:5000/
echo API health:   http://127.0.0.1:5000/api/health
echo ============================================================
python wsgi.py
pause
