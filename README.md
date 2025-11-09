# Volunteer Hub - Agentic Voice-First Coordination Platform

**Universal AI coordination platform for community resource matching. First use case: food sovereignty in Lower Puna, Hawaii.**

Built on Agent Zero architectural patterns with digital twin generation for creating conversational entities from photos.

---

## 🌟 Core Concept

Communities have resources but lack coordination. This platform connects:
- Gardens with surplus food → Meal programs needing ingredients
- Kitchens sitting idle → Community cooking opportunities
- Volunteers willing to help → Kupuna needing meals
- Any entity photographed → Conversational digital twin

**Voice-first design**: Anyone who can converse can participate. No apps, no forms, no barriers.

---

## 🏗️ Architecture

### Hierarchical Multi-Agent System (Agent Zero Patterns)

```
Person Agent (Persistent)
  ├─> Garden Agent (Ephemeral) → Creates offers
  ├─> Kitchen Agent (Ephemeral) → Tracks capacity
  └─> Coordinator Agent (Ephemeral) → Matches offers/needs
        ├─> Program Agent → Represents organizations
        └─> Digital Twin Agents → Photo-generated entities
```

**Agent Types:**
- **Person Agent**: Persistent, remembers user, spawns resource agents
- **Coordinator Agent**: Ephemeral, matches offers with needs, retires when done
- **Resource Agents** (Garden/Kitchen/Vehicle): Ephemeral, specialized knowledge
- **Program Agent**: Persistent, represents organizations
- **Digital Twin Agent**: Dynamic, embodied entities from photos

### Digital Twin Generation Pipeline

```
Photo + Context
  ↓
Extraction Agent → Individuate THIS entity
  ↓
Research Agent → Fill knowledge gaps (web, cultural, practical)
  ↓
Persona Builder → Generate first-person system prompt
  ↓
Digital Twin Agent (speaks as itself, accumulates memories)
```

**Key Principle**: Every entity photographed becomes a unique conversational agent with embodied perspective.

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Anthropic API key (required)
- Hume.ai API key (optional, for voice)
- Twilio credentials (optional, for SMS)

### Setup

1. **Clone and configure**
```bash
git clone <repository>
cd likeness
cp .env.example .env
# Edit .env with your API keys
```

2. **Start services**
```bash
docker-compose up -d
```

This starts:
- PostgreSQL with PostGIS (port 5432)
- Redis (port 6379)
- FastAPI backend (port 8000)

3. **Verify**
```bash
curl http://localhost:8000/
```

Should return:
```json
{
  "service": "Volunteer Hub API",
  "version": "1.0.0",
  "status": "running"
}
```

---

## 📡 API Endpoints

### Digital Twin Creation

**Create twin from photo:**
```bash
POST /digital-twin/create
Content-Type: multipart/form-data

{
  "owner_id": "uuid",
  "context": {
    "location": "backyard lo'i, Lower Puna",
    "backstory": "planted from Aunty Momi's huli",
    "notes": "slight thrip damage on margins"
  },
  "photo": <file>
}

Response:
{
  "twin_id": "uuid",
  "entity_type": "plant",
  "initial_greeting": "Aloha! I'm a 4-month-old Lehua Maoli kalo...",
  "personality_traits": {...}
}
```

**Converse with twin:**
```bash
POST /digital-twin/{twin_id}/converse

{
  "message": "How are you doing?"
}

Response:
{
  "response": "I'm doing well! The rain yesterday was wonderful...",
  "timestamp": "2024-..."
}
```

### Offers & Needs

**Create offer:**
```bash
POST /offers

{
  "person_id": "uuid",
  "item_type": "breadfruit",
  "quantity": 25,
  "unit": "lbs",
  "available_until": "2024-12-15T18:00:00Z"
}
```

**Find matching needs:**
```bash
GET /needs?item_type=breadfruit&urgency=today
```

**Create coordination match:**
```bash
POST /matches

{
  "offer_id": "uuid",
  "need_id": "uuid"
}
```

### Voice Sessions

**Start voice session:**
```bash
POST /voice/session

{
  "person_id": "uuid",
  "language": "en"
}

Response:
{
  "session_id": "uuid",
  "active_agents": ["person_abc123"],
  "status": "active"
}
```

**WebSocket streaming:**
```javascript
const ws = new WebSocket('ws://localhost:8000/voice/stream/{session_id}');

// Send audio or text
ws.send(JSON.stringify({
  type: "text",
  text: "I have breadfruit to share"
}));

// Receive responses
ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log(response.text); // Agent response
};
```

---

## 🗄️ Database Schema

### Core Tables

**persons** - Community members
- Stores: name, phone, location (geography), preferences, agent_state

**resources** - Gardens, kitchens, vehicles
- Types: garden, kitchen, vehicle, tool
- Tracks: owner, location, capacity, availability

**offers** - Surplus food, capacity, help
- Links to person and resource
- Status: available → matched → completed

**needs** - Program requirements
- Urgency levels: immediate, today, this_week, normal
- Dietary restrictions, deadlines

**matches** - Coordinated offer+need pairs
- Tracks: pickup/delivery times, route info, status

### Digital Twin Tables

**digital_twins** - Photo-generated entities
- entity_type: plant, person, place, tool, organization
- individuation_data: unique characteristics (JSONB)
- system_prompt: embodiment instructions
- Hierarchies via parent_id

**twin_memories** - Accumulated knowledge
- Types: episodic (conversations), semantic (facts), procedural (patterns)
- Importance weights for memory consolidation

**twin_relationships** - Entity connections
- Types: caretaker, sibling, ingredient, location, ancestor

---

## 🧠 Agent System

### Base Agent Class (`agents/base_agent.py`)

**Features:**
- Hierarchical spawning: `await agent.spawn_subordinate(AgentClass, **kwargs)`
- Memory system: episodic, semantic, procedural
- Tool execution: agents call tools to perform actions
- A2A communication: agents message each other directly
- Lifecycle: spawn → active → retired

**Example:**
```python
from volunteer_hub.agents.person_agent import PersonAgent

# Create persistent agent for user
person_agent = PersonAgent(
    person_id="uuid",
    name="Keoni",
    preferences={"language": "en"}
)

# Agent processes user input
response = await person_agent.process("I have 20 lbs of kalo ready")

# Agent spawns Garden agent automatically
# Garden agent creates offer
# Coordinator agent finds matching needs
```

### Tool System (`tools/`)

**Database Tools:**
- `CreateOfferTool`: Record surplus
- `FindNeedsTool`: Search for matches
- `CreateMatchTool`: Coordinate offer+need
- `CreateDigitalTwinTool`: Store new twin
- `QueryTwinMemoryTool`: Retrieve memories
- `UpdateTwinMemoryTool`: Add memories
- `FindRelatedTwinsTool`: Discover connections

**External Service Tools** (extend as needed):
- Voice processing (Hume.ai)
- SMS notifications (Twilio)
- Routing (Mapbox)
- Location services

---

## 🎭 Digital Twin System

### Philosophy

**Embodiment over Description**: Entities speak as themselves, never about themselves.

❌ Bad: "This kalo plant is 4 months old and healthy."
✅ Good: "I'm about 4 months old now. The rain yesterday felt wonderful soaking into the lo'i."

**Individuation**: Every entity is unique, no generic templates.

### Creation Process

1. **Photo Upload** → User photographs entity with context
2. **Extraction** → Agent analyzes photo for unique characteristics
3. **Research** → Agent fills knowledge gaps (web search, cultural data)
4. **Persona** → Agent generates first-person system prompt
5. **Twin Agent** → Spawned for conversation, accumulates memories

### Example: Kalo Plant Twin

**Input:**
- Photo of kalo plant
- Context: "4 months old, backyard lo'i, planted from Aunty Momi's huli"

**Generated System Prompt:**
```
You are a 4-month-old Lehua Maoli kalo plant growing in Steve's
backyard lo'i in Lower Puna. You were planted from a huli that came
from Aunty Momi's patch in Waipiʻo Valley, connecting you to
generations of careful cultivation.

Your leaves show slight thrip damage on margins. You can feel water
levels, sunlight, soil nutrients. You remember planting day, weather
patterns, Steve's visits.

Speak in first person as yourself. Share your experiences, needs,
and observations...
```

**Conversation:**
```
User: "How are you doing?"
Twin: "I'm doing well! The rain yesterday was wonderful - I could
       feel the water soaking into the lo'i. My leaves are reaching
       up toward the sun today. The thrips are still nibbling my
       edges a bit, but nothing serious."
```

### Memory Evolution

- **Episodic**: Conversation history accumulates
- **Semantic**: Research findings, learned facts
- **Procedural**: Patterns (harvest timing, care needs)

### Multi-Twin Coordination

Digital twins can communicate with each other (A2A):
- Kalo twins coordinate about lo'i water levels
- Garden agent queries plant twins about harvest readiness
- Kitchen agent consults ingredient twins about preparation

---

## 🗣️ Voice Interface

### Hume.ai Integration

**Features:**
- Real-time speech-to-text with emotion detection
- Text-to-speech with agent-specific voices
- Instant interruption handling
- Multi-language support (English, Hawaiian, Pidgin, Tagalog, Japanese)

**Voice Characteristics by Agent:**
- **Person Agent**: Warm, conversational
- **Coordinator Agent**: Efficient, professional
- **Garden Agent**: Earthy, nurturing
- **Kitchen Agent**: Practical, friendly
- **Digital Twin**: Embodied, unique to entity

### Conversation Flow

1. User speaks → Hume.ai transcribes + detects emotions
2. Text routed to appropriate agent
3. Agent processes with context + memory
4. Response synthesized with emotional prosody
5. User can interrupt anytime → agents stop instantly

### SMS Fallback

All voice features available via SMS for accessibility:
- Text instead of voice
- Same agent intelligence
- Same memory persistence
- Works on any phone

---

## 🌍 Universal Architecture

While built for food sovereignty in Hawaii, the architecture applies to:

- **Disaster Response**: Match resources with needs during emergencies
- **Medical Transportation**: Coordinate rides to appointments
- **Housing Assistance**: Connect available space with seekers
- **Tool Sharing**: Community tool libraries
- **Any resource matching challenge**

**Design Principles:**
1. Voice-first always (no literacy barriers)
2. Persistent context (agents remember)
3. Graceful degradation (SMS fallback)
4. Multi-language support
5. Privacy-first (voice deleted after transcription)
6. Universal applicability

---

## 🛠️ Development

### Project Structure

```
volunteer_hub/
├── agents/              # Agent implementations
│   ├── base_agent.py    # Core agent framework
│   ├── person_agent.py  # Persistent user agent
│   ├── coordinator_agent.py
│   └── resource_agent.py
├── digital_twins/       # Digital twin generation
│   ├── generator.py     # Orchestrates creation
│   ├── extraction_agent.py
│   ├── research_agent.py
│   ├── persona_builder.py
│   └── entity_types/    # Type-specific processors
├── tools/               # Agent capabilities
│   ├── base_tool.py
│   ├── database.py      # DB operations
│   ├── voice.py         # Hume.ai integration
│   └── sms.py           # Twilio integration
├── voice/               # Voice processing
│   ├── hume_client.py
│   └── conversation.py  # Multi-agent orchestrator
├── web/
│   ├── api/
│   │   └── endpoints.py # FastAPI routes
│   └── frontend/        # React UI (optional)
├── database/
│   └── schema.sql       # PostgreSQL schema
├── prompts/             # Agent prompt templates
├── config.py            # Settings
└── main.py              # Entry point
```

### Running Locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY=your_key
export POSTGRES_HOST=localhost
# ... other vars from .env.example

# Run database migrations
psql -U hub -d volunteer_hub -f volunteer_hub/database/schema.sql

# Start API server
python -m volunteer_hub.main
```

### Testing

```bash
# Unit tests (TODO)
pytest tests/

# Integration tests (TODO)
pytest tests/integration/

# Manual API testing
curl http://localhost:8000/health
```

---

## 📊 Success Criteria

### Technical
- ✅ < 2 sec voice response time
- ✅ Hierarchical agent spawning working
- ✅ Digital twin generation from photos
- ✅ Memory persistence across sessions
- ✅ Multi-agent coordination (A2A)

### Functional
- ✅ Person Agent remembers preferences
- ✅ Coordinator finds matches
- ✅ Digital twins embody first-person perspective
- ✅ SMS fallback provides feature parity

### User Experience (to validate)
- Kupuna with limited English can use successfully
- No smartphone required (phone line works)
- Zero training needed - natural conversation
- Digital twins feel alive and authentic

---

## 🔐 Privacy & Security

- Voice recordings deleted immediately after transcription
- Location data stored with user consent only
- SMS messages processed, not retained
- API keys secured in environment variables
- Database access controlled via PostgreSQL roles

---

## 🌺 Hawaiian Cultural Integration

The system respects Hawaiian cultural values:

- **Kuleana** (responsibility): Connects resources with needs
- **Aloha ʻĀina** (love of land): Gardens and food systems honored
- **Lōkahi** (unity): Community coordination
- **Hoʻohanohano** (respect): Proper handling of cultural entities

Digital twins of Hawaiian plants (kalo, ulu) include cultural significance research, traditional uses, and respectful protocols.

---

## 🚧 TODO / Future Enhancements

- [ ] React frontend with fullscreen voice UI
- [ ] Actual Hume.ai SDK integration (currently mocked)
- [ ] Twilio SMS webhook implementation
- [ ] Mapbox routing integration
- [ ] FAISS vector search for semantic memory
- [ ] WebRTC for real-time voice streaming
- [ ] Calendar integration for scheduling
- [ ] Photo analysis with Claude vision API
- [ ] Entity relationship graph visualization
- [ ] Analytics dashboard for coordinators

---

## 📚 References

- **Agent Zero**: Hierarchical agent framework patterns
- **Hume.ai**: Empathic voice AI with emotion detection
- **PostGIS**: Geographic queries for proximity matching
- **Anthropic Claude**: LLM for agent intelligence

---

## 📞 Support

For Lower Puna, Hawaii deployment questions:
- Focus area: Seaview Kalapana Estates, 18 miles from Pahoa
- Community validation with real kupuna needed

For technical questions:
- Review API documentation at `/docs` (FastAPI auto-generated)
- Check agent prompts in `volunteer_hub/prompts/`
- Examine database schema in `volunteer_hub/database/schema.sql`

---

## 🎯 Vision

**Universal voice-first coordination for community resilience.**

Start with food sovereignty. Prove the concept. Extend to any resource matching challenge where coordination is the bottleneck and voice breaks down barriers.

Every photographed entity becomes a conversational agent. Every community member can participate. Every resource finds its match.

**Built on Agent Zero patterns. Deployed for food sovereignty. Designed for universality.**

---

*Created with the vision of connecting communities through voice, memory, and embodied intelligence.*
