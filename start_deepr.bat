@echo off
cd /d "%~dp0"
echo Starting DeepR...
docker compose up -d
if %errorlevel% neq 0 (
    echo Error starting DeepR. Please check if Docker Desktop is running.
    pause
) else (
    echo DeepR started successfully!
    timeout /t 5
)
