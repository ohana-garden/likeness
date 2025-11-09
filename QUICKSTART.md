# Quick Start Guide - Volunteer Hub

## 🚀 Get Running in 5 Minutes

### 1. Prerequisites

```bash
# Install Docker and Docker Compose
# https://docs.docker.com/get-docker/

# Get API Key
# Sign up at https://console.anthropic.com/ for Anthropic API key
```

### 2. Setup

```bash
# Clone repository
git clone https://github.com/ohana-garden/likeness.git
cd likeness

# Configure environment
cp .env.example .env

# Edit .env and add your Anthropic API key
nano .env  # or use your preferred editor
# Set: ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Launch

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 4. Verify

```bash
# Test API
curl http://localhost:8000/

# Should return:
# {
#   "service": "Volunteer Hub API",
#   "version": "1.0.0",
#   "status": "running",
#   "features": {...}
# }

# View API documentation
open http://localhost:8000/docs
```

## 📸 Try Digital Twin Creation

### Example: Create a Kalo Plant Twin

```bash
# Create a test photo (or use your own)
# For testing, we'll simulate with text context

curl -X POST http://localhost:8000/digital-twin/create \
  -F "owner_id=test-user-123" \
  -F "context={\"location\":\"backyard loi, Lower Puna\",\"backstory\":\"4 months old, planted from Aunty Momi's huli\",\"notes\":\"healthy, slight thrip damage\"}" \
  -F "photo=@/path/to/kalo_photo.jpg"

# Response includes:
# - twin_id: unique identifier
# - initial_greeting: first-person introduction
# - personality_traits: entity characteristics
```

### Converse with the Twin

```bash
# Get the twin_id from creation response
TWIN_ID="your-twin-id-here"

curl -X POST http://localhost:8000/digital-twin/$TWIN_ID/converse \
  -H "Content-Type: application/json" \
  -d '{"message": "How are you doing today?"}'

# Twin responds in first-person:
# "I'm doing well! The rain yesterday was wonderful - I could feel
#  the water soaking into the lo'i..."
```

## 🍞 Create Offer/Need/Match Flow

### 1. Create an Offer

```bash
curl -X POST http://localhost:8000/offers \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "test-user-123",
    "item_type": "breadfruit",
    "quantity": 25,
    "unit": "lbs",
    "available_until": "2024-12-20T18:00:00Z"
  }'

# Returns: {"offer_id": "...", "message": "Offer created: 25 lbs of breadfruit"}
```

### 2. Create a Need

```bash
# First, let's create this via database (in production, programs would create these)
# For now, we'll search for existing needs

curl http://localhost:8000/needs?item_type=breadfruit
```

### 3. Create a Match

```bash
# With offer_id and need_id:
curl -X POST http://localhost:8000/matches \
  -H "Content-Type: application/json" \
  -d '{
    "offer_id": "offer-uuid-here",
    "need_id": "need-uuid-here"
  }'

# Coordinator agent spawns, evaluates match, creates coordination
```

## 🎙️ Voice Session (Development Mode)

### Start Voice Session

```bash
curl -X POST http://localhost:8000/voice/session \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "test-user-123",
    "language": "en"
  }'

# Returns session_id for WebSocket connection
```

### Connect via WebSocket

```javascript
// In browser console or Node.js
const ws = new WebSocket('ws://localhost:8000/voice/stream/SESSION_ID');

ws.onopen = () => {
  // Send text (voice transcription would go here)
  ws.send(JSON.stringify({
    type: "text",
    text: "I have 20 pounds of breadfruit ready to share"
  }));
};

ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log(`${response.speaker_type}: ${response.text}`);
};
```

## 🗄️ Database Access

### Connect to PostgreSQL

```bash
# Access database directly
docker-compose exec postgres psql -U hub -d volunteer_hub

# Example queries:
SELECT * FROM persons;
SELECT * FROM digital_twins;
SELECT * FROM offers WHERE status = 'available';

# Geographic query (find offers within 10km)
SELECT * FROM find_nearby_offers(
  ST_SetSRID(ST_MakePoint(-154.9, 19.5), 4326)::geography,
  10.0
);
```

## 🧪 Testing Scenarios

### Scenario 1: Garden Harvest Flow

```bash
# 1. Person mentions harvest
# "I have kalo ready to harvest"
# → Person Agent spawns Garden Agent
# → Garden Agent asks for details
# → Creates offer

# 2. Coordinator searches for matches
# → Finds meal program needing kalo
# → Proposes match with distance/timing

# 3. Confirmation and coordination
# → Match created
# → Notifications sent
```

### Scenario 2: Digital Twin Interaction

```bash
# 1. Photograph kalo plant with context
# → Extraction Agent individuates characteristics
# → Research Agent fills cultural/practical knowledge
# → Persona Builder creates embodied prompt
# → Twin spawned with first-person voice

# 2. Conversation builds relationship
# User: "How's the weather affecting you?"
# Twin: "The heavy rains yesterday were wonderful..."
# → Episodic memory accumulates
# → Relationship deepens over time

# 3. Multi-twin coordination
# → Garden Agent consults Plant Twin about harvest readiness
# → Kitchen Agent asks Plant Twin about preparation
# → A2A communication between twins
```

## 🛠️ Development

### Run Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export ANTHROPIC_API_KEY=your_key
export POSTGRES_HOST=localhost
# ... other vars

# Run database locally
brew install postgresql postgis  # or apt-get
createdb volunteer_hub
psql volunteer_hub -f volunteer_hub/database/schema.sql

# Start API
python -m volunteer_hub.main
```

### Hot Reload During Development

```bash
# Docker Compose is configured for hot reload
# Edit files in volunteer_hub/ and changes reflect immediately

docker-compose logs -f api  # Watch for reload messages
```

## 🐛 Troubleshooting

### API won't start
```bash
# Check logs
docker-compose logs api

# Common issues:
# - Missing ANTHROPIC_API_KEY in .env
# - Port 8000 already in use
# - Database not ready (wait 10 seconds, try again)
```

### Database connection errors
```bash
# Ensure PostgreSQL is healthy
docker-compose ps postgres

# Should show "healthy" status
# If not, check logs:
docker-compose logs postgres
```

### Can't create digital twin
```bash
# Check that photo file exists and is accessible
# Verify owner_id is valid UUID format
# Check API logs for detailed error
docker-compose logs api | grep ERROR
```

## 📊 Monitoring

### View Active Agents
```bash
curl http://localhost:8000/debug/agents

# Shows all spawned agents
```

### View Active Conversations
```bash
curl http://localhost:8000/debug/conversations

# Shows active voice sessions
```

### Database Statistics
```bash
docker-compose exec postgres psql -U hub -d volunteer_hub -c "
SELECT
  'Persons' as table_name, COUNT(*) as count FROM persons
UNION ALL
SELECT 'Digital Twins', COUNT(*) FROM digital_twins
UNION ALL
SELECT 'Offers', COUNT(*) FROM offers
UNION ALL
SELECT 'Active Matches', COUNT(*) FROM matches WHERE status != 'completed';
"
```

## 🎯 Next Steps

1. **Add Real Photos**: Test digital twin generation with actual plant photos
2. **Create Test Users**: Set up several personas to simulate community
3. **Build Frontend**: React UI for voice interface (see TODO)
4. **Deploy to Hawaii**: Test with actual kupuna in Lower Puna
5. **Integrate Hume.ai**: Replace mock voice client with real SDK
6. **Add Twilio**: Enable SMS fallback

## 🌺 Hawaiian Context Testing

### Test with Hawaiian Entities

```bash
# Kalo (taro) varieties
curl -X POST http://localhost:8000/digital-twin/create \
  -F "context={\"type\":\"Lehua Maoli kalo\",\"location\":\"Waipio Valley\"}" \
  -F "photo=@kalo_photo.jpg"

# Breadfruit tree
curl -X POST http://localhost:8000/digital-twin/create \
  -F "context={\"type\":\"ulu tree\",\"age\":\"15 years\",\"location\":\"backyard\"}" \
  -F "photo=@ulu_photo.jpg"

# Traditional imu
curl -X POST http://localhost:8000/digital-twin/create \
  -F "context={\"type\":\"imu\",\"last_used\":\"last weekend\",\"condition\":\"good\"}" \
  -F "photo=@imu_photo.jpg"
```

### Language Testing

```bash
# Test Hawaiian language support
curl -X POST http://localhost:8000/voice/session \
  -d '{"person_id": "test", "language": "haw"}'

# Test Pidgin
curl -X POST http://localhost:8000/voice/session \
  -d '{"person_id": "test", "language": "en"}' # Pidgin uses 'en' code
```

## 📚 Learn More

- Full Documentation: See [README.md](README.md)
- API Docs: http://localhost:8000/docs (when running)
- Database Schema: [volunteer_hub/database/schema.sql](volunteer_hub/database/schema.sql)
- Agent Prompts: [volunteer_hub/prompts/](volunteer_hub/prompts/)

## 🤝 Support

- Technical Issues: Check logs, review README
- Hawaii Deployment: Focus on Seaview Kalapana Estates, 18mi from Pahoa
- Community Validation: Test with real kupuna before wide deployment

---

**You're ready to start coordinating community resources with voice and embodied AI!**

🌺 Aloha ʻĀina - Love of the Land
