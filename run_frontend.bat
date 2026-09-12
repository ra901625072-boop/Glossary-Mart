@echo off
title e Grossary - Frontend Server (Port 3000)
echo ============================================================
echo Starting e Grossary Static Frontend on port 3000...
echo URL: http://localhost:3000/
echo Connected to backend: http://127.0.0.1:5000/
echo ============================================================
python -m http.server 3000 --directory frontend
pause
