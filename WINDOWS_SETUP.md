# 🪟 Windows Setup Guide - Volunteer Hub

Complete guide for running Volunteer Hub on Windows with Docker Desktop.

---

## 📋 Prerequisites

### 1. Install Docker Desktop for Windows

```powershell
# Download from: https://www.docker.com/products/docker-desktop/

# After installation, verify:
docker --version
docker-compose --version
```

### 2. Install Python (for testing)

```powershell
# Download Python 3.11+ from: https://www.python.org/downloads/

# Or use winget:
winget install Python.Python.3.11

# Verify:
python --version
pip --version
```

### 3. Get Anthropic API Key

1. Sign up at https://console.anthropic.com/
2. Create an API key
3. Copy it (starts with `sk-ant-`)

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone Repository (if needed)

```powershell
# If you haven't cloned yet:
git clone https://github.com/ohana-garden/likeness.git
cd likeness

# Or navigate to existing directory:
cd path\to\likeness
```

### Step 2: Configure Environment

```powershell
# Copy example environment file
copy .env.example .env

# Edit with Notepad
notepad .env

# Add your API key:
# ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Save and close
```

### Step 3: Start Services

```powershell
# Start all containers
docker-compose up -d

# Check status (should show all "Up")
docker-compose ps

# Watch logs to confirm startup
docker-compose logs -f api

# Press Ctrl+C to stop watching logs
```

### Step 4: Run Tests

```powershell
# Install Python dependencies
pip install requests

# Run automated test suite
python test_volunteer_hub.py

# Or run interactive mode
python test_volunteer_hub.py interactive
```

---

## 🧪 Using the Test Suite

### Automated Test Mode (Default)

```powershell
python test_volunteer_hub.py
```

This will automatically test:
- ✓ API connectivity
- ✓ Health checks
- ✓ Offer creation
- ✓ Need searching
- ✓ Digital twin generation
- ✓ Twin conversation
- ✓ Memory retrieval
- ✓ Voice session creation

**Sample Output:**
```
============================================================
   VOLUNTEER HUB API TEST SUITE FOR WINDOWS
============================================================

============================================================
1. Testing API Connection
============================================================

✓ API is running!
ℹ Service: Volunteer Hub API
ℹ Version: 1.0.0
ℹ Status: running

============================================================
5. Testing Digital Twin Creation (Context Only)
============================================================

ℹ Creating digital twin with context:
{
  "location": "backyard lo'i, Lower Puna, Hawaii",
  "backstory": "4-month-old Lehua Maoli kalo...",
  ...
}

✓ Digital twin created!
ℹ Twin ID: abc-123-def-456
ℹ Entity Type: plant

Initial Greeting:
Aloha! I'm a 4-month-old Lehua Maoli kalo plant growing...
```

### Interactive Mode

```powershell
python test_volunteer_hub.py interactive
```

Available commands:
- `test` - Run all tests
- `offer` - Create an offer
- `twin` - Create digital twin
- `talk` - Talk to twin
- `session` - Create voice session
- `status` - Check API status
- `help` - Show commands
- `quit` - Exit

**Example Session:**
```
> twin
Creating digital twin...
✓ Digital twin created!
ℹ Twin ID: abc-123

> talk
Your message: How are you doing?
Twin Response: I'm doing well! The rain yesterday was wonderful...

> quit
```

---

## 🌐 Access API Documentation

### Open Interactive API Docs

```powershell
# Start your browser with API docs
start http://localhost:8000/docs

# Or alternative docs
start http://localhost:8000/redoc
```

You can test all endpoints directly in the browser!

---

## 🗄️ Database Access

### Method 1: Command Line

```powershell
# Connect to PostgreSQL
docker-compose exec postgres psql -U hub -d volunteer_hub

# Run SQL queries:
# List tables
\dt

# View digital twins
SELECT id, entity_type, entity_subtype FROM digital_twins;

# View offers
SELECT * FROM offers;

# Exit
\q
```

### Method 2: GUI Tool (Recommended)

**Install DBeaver (Free):**
```powershell
winget install dbeaver.dbeaver
```

**Connect to Database:**
- Host: `localhost`
- Port: `5432`
- Database: `volunteer_hub`
- Username: `hub`
- Password: `password`

---

## 📸 Testing with Photos

### Create Digital Twin from Photo

```powershell
# Place a photo in the project directory (e.g., plant.jpg)

# Create a Python test script
python
```

```python
import requests
import json

# Read the photo
with open('plant.jpg', 'rb') as f:
    files = {'photo': ('plant.jpg', f, 'image/jpeg')}
    data = {
        'owner_id': 'test-user',
        'context': json.dumps({
            'location': 'backyard garden',
            'type': 'kalo plant',
            'age': '4 months'
        })
    }

    response = requests.post(
        'http://localhost:8000/digital-twin/create',
        files=files,
        data=data
    )

    print(response.json())
```

### Or Use PowerShell

```powershell
# Using curl (available in Windows 10+)
curl.exe -X POST http://localhost:8000/digital-twin/create `
  -F "owner_id=test-user" `
  -F "context={\"location\":\"backyard\",\"type\":\"kalo\"}" `
  -F "photo=@plant.jpg"
```

---

## 🔍 Monitoring & Logs

### View Real-Time Logs

```powershell
# All services
docker-compose logs -f

# Just API
docker-compose logs -f api

# Just database
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 api
```

### Save Logs to File

```powershell
# Save API logs
docker-compose logs api > api_logs.txt

# Open in editor
notepad api_logs.txt
```

### Check Container Status

```powershell
# Status of all containers
docker-compose ps

# Detailed info
docker ps

# Resource usage
docker stats
```

---

## 🛑 Stop/Restart/Clean

### Stop Services

```powershell
# Stop all containers (data preserved)
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v
```

### Restart Services

```powershell
# Restart everything
docker-compose restart

# Restart just API (after code changes)
docker-compose restart api

# Rebuild and restart (after dependency changes)
docker-compose up -d --build
```

### Clean Everything

```powershell
# Stop and remove everything
docker-compose down -v

# Remove Docker cache
docker system prune -a

# Fresh start
docker-compose up -d --build
```

---

## 🐛 Common Windows Issues

### Issue: Docker Desktop Not Starting

**Fix:**
1. Enable WSL 2 in Windows Features
2. Update Windows to latest version
3. Check Docker Desktop settings → General → "Use WSL 2"

### Issue: Port Already in Use

**Check what's using port 8000:**
```powershell
netstat -ano | findstr :8000
```

**Change port in docker-compose.yml:**
```yaml
api:
  ports:
    - "8001:8000"  # Use 8001 instead
```

### Issue: Line Ending Errors

**Fix Git line endings:**
```powershell
git config --global core.autocrlf false
git rm --cached -r .
git reset --hard
```

### Issue: API Won't Connect

**Check firewall:**
```powershell
# Allow Docker Desktop through firewall
# Windows Security → Firewall → Allow an app → Docker Desktop
```

**Verify containers are running:**
```powershell
docker-compose ps

# Should show all containers as "Up"
# If not, check logs:
docker-compose logs
```

### Issue: Database Connection Failed

**Wait for database to be ready:**
```powershell
# Database takes ~10 seconds to initialize
# Wait and try again

# Check database health
docker-compose ps postgres
# Should show "healthy"
```

### Issue: Out of Disk Space

**Clean Docker:**
```powershell
# Remove unused images/containers
docker system prune -a

# Check disk usage
docker system df
```

---

## 📝 Example Workflows

### Workflow 1: Create Kalo Twin and Converse

```powershell
# Start services
docker-compose up -d

# Run Python interactive mode
python test_volunteer_hub.py interactive

# In interactive mode:
> twin
# Creates kalo digital twin

> talk
Your message: Tell me about yourself
# Twin introduces itself

> talk
Your message: What do you need?
# Twin expresses needs

> quit
```

### Workflow 2: Create Offer and Find Matches

```python
# create_offer.py
import requests

# Create offer
offer = {
    "person_id": "user123",
    "item_type": "breadfruit",
    "quantity": 30,
    "unit": "lbs"
}

response = requests.post("http://localhost:8000/offers", json=offer)
print(f"Offer created: {response.json()}")

# Find matching needs
response = requests.get("http://localhost:8000/needs?item_type=breadfruit")
print(f"Matching needs: {response.json()}")
```

Run it:
```powershell
python create_offer.py
```

### Workflow 3: Voice Session with Multiple Agents

```python
# voice_session.py
import requests
import json

# Create session
session = requests.post(
    "http://localhost:8000/voice/session",
    json={"person_id": "user123", "language": "en"}
).json()

print(f"Session ID: {session['session_id']}")
print(f"Active agents: {session['active_agents']}")

# In production, you'd connect via WebSocket here
# For now, we can see the session was created
```

---

## 🎯 Next Steps

### 1. Explore API Endpoints

Open http://localhost:8000/docs in browser and try:
- Create digital twins
- Create offers and needs
- Search for matches
- Start voice sessions

### 2. Customize Configuration

Edit `.env` to enable features:
```env
ENABLE_VOICE=true
ENABLE_SMS_FALLBACK=true
ENABLE_DIGITAL_TWINS=true
```

### 3. Add Real Photos

Test digital twin creation with actual plant photos:
1. Take photo of a plant
2. Save as `test_plant.jpg`
3. Run test suite - it will automatically use the photo

### 4. Build Frontend (Optional)

```powershell
cd volunteer_hub\web\frontend

# Install dependencies (if React app is set up)
npm install

# Start dev server
npm start
```

---

## 📚 Additional Resources

### Official Documentation
- **README.md** - Complete platform documentation
- **QUICKSTART.md** - Cross-platform quick start guide
- **API Docs** - http://localhost:8000/docs (when running)

### Docker Desktop Help
- Settings → Resources → Adjust memory/CPU
- Settings → Docker Engine → View config
- Troubleshoot → Reset to factory defaults (if needed)

### Python Dependencies
```powershell
# Install all testing dependencies
pip install requests colorama

# Or create requirements
pip install -r requirements.txt
```

---

## 💡 Tips for Windows Users

1. **Use Windows Terminal** instead of PowerShell
   - Better colors, tabs, copy/paste
   - Install from Microsoft Store

2. **Set up PATH properly**
   - Python should be in PATH
   - Docker Desktop adds itself automatically

3. **Enable Developer Mode** (optional)
   - Settings → Update & Security → For Developers
   - Enables symlinks and other dev features

4. **Use VS Code** for editing
   - Install "Docker" extension
   - Install "Python" extension
   - View logs, manage containers from IDE

5. **Keep Docker Desktop Running**
   - Set to start on Windows startup
   - Monitor from system tray

---

## ✅ Verification Checklist

Before reporting issues, verify:

- [ ] Docker Desktop is running (green icon in tray)
- [ ] `docker --version` works
- [ ] `.env` file exists with `ANTHROPIC_API_KEY`
- [ ] `docker-compose ps` shows all containers as "Up"
- [ ] `python test_volunteer_hub.py` completes without errors
- [ ] http://localhost:8000/ returns JSON response
- [ ] Database is accessible: `docker-compose exec postgres psql -U hub -d volunteer_hub`

---

## 🆘 Getting Help

### Check Logs First
```powershell
docker-compose logs --tail=100
```

### Common Log Locations
- Docker Desktop logs: Click Docker icon → Troubleshoot → View logs
- Application logs: `docker-compose logs api`
- Database logs: `docker-compose logs postgres`

### Test API Manually
```powershell
# Simple connectivity test
curl http://localhost:8000/

# Or in PowerShell
Invoke-RestMethod -Uri http://localhost:8000/
```

---

**You're all set! Run `python test_volunteer_hub.py` to start testing! 🚀**
