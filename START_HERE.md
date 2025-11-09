# 🚀 ONE-CLICK SETUP - START HERE

## **Windows Users: Just Double-Click!**

### **Option 1: Batch File (Recommended)**
```
📁 Double-click: setup.bat
```

### **Option 2: PowerShell (Alternative)**
Right-click `setup.ps1` → Run with PowerShell

---

## What the Setup Does Automatically:

✅ Checks if Docker is running
✅ Creates `.env` configuration file
✅ Asks for your Anthropic API key (one time)
✅ Installs Python dependencies
✅ Starts all services (PostgreSQL, Redis, API)
✅ Waits for everything to be ready
✅ Runs automated tests
✅ Opens API documentation in your browser

**Total time: ~2 minutes** ⏱️

---

## What You Need:

1. **Docker Desktop** - Must be running (green whale icon in system tray)
   - Download: https://www.docker.com/products/docker-desktop/

2. **Anthropic API Key** - Free to get!
   - Sign up: https://console.anthropic.com/
   - Copy the key (starts with `sk-ant-`)

3. **Python** (Optional - for testing)
   - Download: https://www.python.org/downloads/

---

## After Setup:

### 🌐 Open API Documentation
```
http://localhost:8000/docs
```
Try all features directly in your browser!

### 🧪 Run Tests
```powershell
python test_volunteer_hub.py
```

### 💬 Interactive Mode
```powershell
python test_volunteer_hub.py interactive
```

Then type:
- `twin` - Create a digital twin
- `talk` - Converse with it
- `offer` - Create an offer
- `help` - See all commands

### 📊 View Logs
```powershell
docker-compose logs -f api
```

### 🛑 Stop Services
```powershell
docker-compose down
```

---

## Troubleshooting

### "Docker is not running"
→ Start Docker Desktop from Start Menu
→ Wait for green whale icon in system tray

### "Port already in use"
→ Stop other services using port 8000
→ Or edit `docker-compose.yml` to use different port

### Setup fails or errors
→ Run: `docker-compose down`
→ Double-click `setup.bat` again

---

## What This Platform Does

**Volunteer Hub** is a voice-first AI coordination platform that:

🎙️ **Voice-First Design** - Anyone who can speak can participate
🤖 **Multi-Agent System** - Intelligent agents coordinate resources
🎭 **Digital Twins** - Photograph anything, it becomes conversational
🌺 **Hawaiian Food Sovereignty** - Connects gardens → kupuna → meals
🌍 **Universal** - Works for disaster response, medical, housing, etc.

### Example Use Cases:

**Digital Twin:**
1. Photograph your kalo plant
2. Add context: "4 months old, backyard lo'i"
3. Twin introduces itself in first-person
4. Have conversations, it remembers and learns

**Resource Matching:**
1. "I have 20 lbs of breadfruit ready"
2. System finds programs needing breadfruit
3. Coordinates pickup and delivery
4. All via voice or SMS

---

## Quick Commands Reference

```powershell
# Start everything
.\setup.bat

# Run tests
python test_volunteer_hub.py

# Interactive chat
python test_volunteer_hub.py interactive

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Stop everything
docker-compose down

# Fresh restart
docker-compose down -v
.\setup.bat
```

---

## Files You Should Know About

- **`setup.bat`** - One-click setup (Windows batch)
- **`setup.ps1`** - One-click setup (PowerShell)
- **`test_volunteer_hub.py`** - Python test suite
- **`docker-compose.yml`** - Service configuration
- **`.env`** - Your API keys (created by setup)
- **`README.md`** - Full documentation
- **`WINDOWS_SETUP.md`** - Detailed Windows guide
- **`QUICKSTART.md`** - Cross-platform guide

---

## Need Help?

1. **Read the docs:**
   - Full guide: `README.md`
   - Windows specific: `WINDOWS_SETUP.md`

2. **Check logs:**
   ```powershell
   docker-compose logs
   ```

3. **Verify services:**
   ```powershell
   docker-compose ps
   ```

4. **Test API manually:**
   ```powershell
   curl http://localhost:8000/
   ```

---

## 🎯 Ready to Start?

### **→ Double-click `setup.bat` now! ←**

That's it! The script will guide you through everything.

---

**Built with Agent Zero patterns for universal community coordination through voice and embodied AI.**

🌺 Aloha ʻĀina - Love of the Land
