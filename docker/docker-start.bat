@echo off
REM Docker Startup Script for Windows (Batch)
REM Run this to start the application in Docker

echo.
echo ================================
echo  Starting Docker Containers
echo ================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Copying .env.example to .env...
    copy .env.example .env
    echo.
    echo Please edit .env and add your API keys:
    echo    notepad .env
    echo.
    pause
)

echo Building and starting containers...
echo.
docker-compose up -d --build

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start containers!
    echo Check logs with: docker-compose logs
    pause
    exit /b 1
)

echo.
echo ================================
echo  Application Started!
echo ================================
echo.
echo Frontend:  http://localhost:3000
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo View logs:  docker-compose logs -f
echo Stop:       docker-compose down
echo.
pause
