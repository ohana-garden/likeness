@echo off
REM ============================================================
REM  VOLUNTEER HUB - ONE-CLICK SETUP FOR WINDOWS
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo    VOLUNTEER HUB - ONE-CLICK SETUP
echo ============================================================
echo.

REM Check if Docker is running
echo [1/7] Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo.
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker is running
echo.

REM Check if .env exists
echo [2/7] Checking environment configuration...
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env >nul

    echo.
    echo ============================================================
    echo  ANTHROPIC API KEY REQUIRED
    echo ============================================================
    echo.
    echo You need an Anthropic API key to use this platform.
    echo.
    echo Get your key at: https://console.anthropic.com/
    echo.
    set /p api_key="Enter your Anthropic API key (sk-ant-...): "

    if "!api_key!"=="" (
        echo [ERROR] API key is required!
        pause
        exit /b 1
    )

    REM Update .env file with API key
    powershell -Command "(Get-Content .env) -replace 'ANTHROPIC_API_KEY=your_anthropic_api_key_here', 'ANTHROPIC_API_KEY=!api_key!' | Set-Content .env"
    echo [OK] API key configured
) else (
    echo [OK] .env file exists
)
echo.

REM Check if Python is installed
echo [3/7] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Python not found!
    echo.
    echo Python is recommended for testing but not required.
    echo Download from: https://www.python.org/downloads/
    echo.
    set PYTHON_AVAILABLE=0
) else (
    echo [OK] Python is installed
    set PYTHON_AVAILABLE=1
)
echo.

REM Install Python dependencies if Python is available
if %PYTHON_AVAILABLE%==1 (
    echo [4/7] Installing Python dependencies...
    pip install requests >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Could not install Python dependencies
        echo You can install manually later: pip install requests
    ) else (
        echo [OK] Python dependencies installed
    )
    echo.
) else (
    echo [4/7] Skipping Python dependencies (Python not available)
    echo.
)

REM Stop any existing containers
echo [5/7] Cleaning up old containers...
docker-compose down >nul 2>&1
echo [OK] Cleanup complete
echo.

REM Start Docker containers
echo [6/7] Starting Volunteer Hub services...
echo This may take a minute on first run (downloading images)...
echo.
docker-compose up -d

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start services!
    echo.
    echo Check the error messages above.
    pause
    exit /b 1
)

echo.
echo [OK] Services starting...
echo.

REM Wait for services to be healthy
echo [7/7] Waiting for services to be ready...
timeout /t 5 /nobreak >nul

REM Check if API is responding
set MAX_RETRIES=30
set RETRY_COUNT=0

:wait_loop
curl -s http://localhost:8000/ >nul 2>&1
if errorlevel 1 (
    set /a RETRY_COUNT+=1
    if !RETRY_COUNT! GEQ %MAX_RETRIES% (
        echo.
        echo [WARNING] API is taking longer than expected to start
        echo You can check status with: docker-compose logs api
        goto skip_test
    )
    timeout /t 1 /nobreak >nul
    goto wait_loop
)

echo [OK] API is ready!
echo.

REM Run tests if Python is available
if %PYTHON_AVAILABLE%==1 (
    echo.
    echo ============================================================
    echo  RUNNING TESTS
    echo ============================================================
    echo.
    python test_volunteer_hub.py
    echo.
)

:skip_test

REM Success message
echo.
echo ============================================================
echo  SETUP COMPLETE!
echo ============================================================
echo.
echo Volunteer Hub is now running at: http://localhost:8000
echo.
echo What you can do now:
echo.
echo   1. View API docs:
echo      start http://localhost:8000/docs
echo.
echo   2. Run tests:
echo      python test_volunteer_hub.py
echo.
echo   3. Interactive mode:
echo      python test_volunteer_hub.py interactive
echo.
echo   4. Check logs:
echo      docker-compose logs -f api
echo.
echo   5. Stop services:
echo      docker-compose down
echo.
echo Services running:
docker-compose ps
echo.

REM Ask if user wants to open browser
set /p open_browser="Open API documentation in browser? (Y/n): "
if /i "!open_browser!"=="y" (
    start http://localhost:8000/docs
) else if "!open_browser!"=="" (
    start http://localhost:8000/docs
)

echo.
echo Press any key to exit setup...
pause >nul
