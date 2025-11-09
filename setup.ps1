# ============================================================
#  VOLUNTEER HUB - ONE-CLICK SETUP FOR WINDOWS (PowerShell)
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   VOLUNTEER HUB - ONE-CLICK SETUP" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Function to write colored output
function Write-Step {
    param($Step, $Total, $Message)
    Write-Host "[$Step/$Total] " -NoNewline -ForegroundColor Yellow
    Write-Host $Message
}

function Write-Success {
    param($Message)
    Write-Host "[OK] " -NoNewline -ForegroundColor Green
    Write-Host $Message
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] " -NoNewline -ForegroundColor Red
    Write-Host $Message
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] " -NoNewline -ForegroundColor Yellow
    Write-Host $Message
}

# Step 1: Check Docker
Write-Step 1 7 "Checking Docker..."
try {
    docker info | Out-Null
    Write-Success "Docker is running"
    Write-Host ""
} catch {
    Write-Error "Docker is not running!"
    Write-Host ""
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 2: Check environment
Write-Step 2 7 "Checking environment configuration..."
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Gray
    Copy-Item .env.example .env

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host " ANTHROPIC API KEY REQUIRED" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You need an Anthropic API key to use this platform."
    Write-Host ""
    Write-Host "Get your key at: " -NoNewline
    Write-Host "https://console.anthropic.com/" -ForegroundColor Blue
    Write-Host ""

    $apiKey = Read-Host "Enter your Anthropic API key (sk-ant-...)"

    if ([string]::IsNullOrWhiteSpace($apiKey)) {
        Write-Error "API key is required!"
        Read-Host "Press Enter to exit"
        exit 1
    }

    # Update .env file
    (Get-Content .env) -replace 'ANTHROPIC_API_KEY=your_anthropic_api_key_here', "ANTHROPIC_API_KEY=$apiKey" | Set-Content .env
    Write-Success "API key configured"
} else {
    Write-Success ".env file exists"
}
Write-Host ""

# Step 3: Check Python
Write-Step 3 7 "Checking Python..."
$pythonAvailable = $true
try {
    python --version | Out-Null
    Write-Success "Python is installed"
} catch {
    Write-Warning "Python not found!"
    Write-Host ""
    Write-Host "Python is recommended for testing but not required." -ForegroundColor Gray
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Blue
    $pythonAvailable = $false
}
Write-Host ""

# Step 4: Install Python dependencies
if ($pythonAvailable) {
    Write-Step 4 7 "Installing Python dependencies..."
    try {
        pip install requests 2>&1 | Out-Null
        Write-Success "Python dependencies installed"
    } catch {
        Write-Warning "Could not install Python dependencies"
        Write-Host "You can install manually later: pip install requests" -ForegroundColor Gray
    }
} else {
    Write-Step 4 7 "Skipping Python dependencies (Python not available)"
}
Write-Host ""

# Step 5: Cleanup
Write-Step 5 7 "Cleaning up old containers..."
docker-compose down 2>&1 | Out-Null
Write-Success "Cleanup complete"
Write-Host ""

# Step 6: Start services
Write-Step 6 7 "Starting Volunteer Hub services..."
Write-Host "This may take a minute on first run (downloading images)..." -ForegroundColor Gray
Write-Host ""

docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Error "Failed to start services!"
    Write-Host ""
    Write-Host "Check the error messages above." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Success "Services starting..."
Write-Host ""

# Step 7: Wait for API
Write-Step 7 7 "Waiting for services to be ready..."
Start-Sleep -Seconds 5

$maxRetries = 30
$retryCount = 0
$apiReady = $false

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 1 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $apiReady = $true
            break
        }
    } catch {
        $retryCount++
        Start-Sleep -Seconds 1
    }
}

if ($apiReady) {
    Write-Success "API is ready!"
    Write-Host ""
} else {
    Write-Warning "API is taking longer than expected to start"
    Write-Host "You can check status with: docker-compose logs api" -ForegroundColor Gray
}

# Run tests if Python available
if ($pythonAvailable -and $apiReady) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host " RUNNING TESTS" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    python test_volunteer_hub.py
}

# Success message
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Volunteer Hub is now running at: " -NoNewline
Write-Host "http://localhost:8000" -ForegroundColor Blue
Write-Host ""
Write-Host "What you can do now:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. View API docs:" -ForegroundColor Yellow
Write-Host "     start http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Run tests:" -ForegroundColor Yellow
Write-Host "     python test_volunteer_hub.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Interactive mode:" -ForegroundColor Yellow
Write-Host "     python test_volunteer_hub.py interactive" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Check logs:" -ForegroundColor Yellow
Write-Host "     docker-compose logs -f api" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Stop services:" -ForegroundColor Yellow
Write-Host "     docker-compose down" -ForegroundColor Gray
Write-Host ""
Write-Host "Services running:" -ForegroundColor Cyan
docker-compose ps
Write-Host ""

# Ask to open browser
$openBrowser = Read-Host "Open API documentation in browser? (Y/n)"
if ([string]::IsNullOrWhiteSpace($openBrowser) -or $openBrowser -eq "Y" -or $openBrowser -eq "y") {
    Start-Process "http://localhost:8000/docs"
}

Write-Host ""
Write-Host "Setup complete! Press Enter to exit..." -ForegroundColor Green
Read-Host
