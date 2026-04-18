@echo off
chcp 65001 >nul
echo Starting API (uvicorn) in a new window...
start "demo-api" cmd /k "cd /d %~dp0 && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
echo Starting ngrok in a new window...
start "demo-ngrok" cmd /k "ngrok http 8000"
echo.
echo 1) Copy HTTPS URL from ngrok into WEBAPP_URL in your .env file
echo 2) Then run the bot: python main.py
echo.
pause
