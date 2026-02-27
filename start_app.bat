@echo off
echo Starting Modern Recipe App Backend Server...
start "Recipe Backend" cmd /c "cd backend && python server.py"

echo Starting Modern Recipe App Frontend Server...
start "Recipe Frontend" cmd /c "cd frontend && python -m http.server 8000"

echo Opening Web App in Browser...
timeout /t 2 /nobreak >nul
start http://localhost:8000

echo App is now running! 
echo Keep the two small terminal windows open to keep the server alive.
echo Press any key to exit this launcher menu.
pause >nul
