"""
FastAPI Endpoints for Volunteer Hub
Voice sessions, digital twins, offers, needs, coordination
"""
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime

from volunteer_hub.config import settings
from volunteer_hub.digital_twins.generator import DigitalTwinGenerator, DigitalTwinAgent
from volunteer_hub.agents.person_agent import PersonAgent
from volunteer_hub.agents.coordinator_agent import CoordinatorAgent
from volunteer_hub.voice.conversation import MultiAgentConversation
from volunteer_hub.tools.database import (
    CreateOfferTool,
    FindNeedsTool,
    CreateMatchTool,
    QueryTwinMemoryTool
)


# Initialize FastAPI
app = FastAPI(
    title="Volunteer Hub API",
    description="Voice-first AI coordination platform for community resource matching",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ======================
# REQUEST/RESPONSE MODELS
# ======================

class CreatePersonRequest(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    languages: List[str] = ["en"]
    location: Optional[Dict[str, float]] = None  # {"lat": x, "lon": y}
    preferences: Dict[str, Any] = {}


class CreateOfferRequest(BaseModel):
    person_id: str
    item_type: str
    quantity: float
    unit: str = "lbs"
    resource_id: Optional[str] = None
    available_until: Optional[str] = None


class CreateNeedRequest(BaseModel):
    program_id: str
    item_type: str
    quantity: float
    unit: str = "lbs"
    urgency: str = "normal"
    dietary_restrictions: List[str] = []


class DigitalTwinCreateRequest(BaseModel):
    owner_id: str
    context: Dict[str, Any]  # User-provided context about entity


class ConverseWithTwinRequest(BaseModel):
    message: str


class VoiceSessionRequest(BaseModel):
    person_id: str
    language: str = "en"


# ======================
# GLOBAL STATE
# ======================

# Active agent sessions
active_agents: Dict[str, Any] = {}

# Active voice conversations
active_conversations: Dict[str, MultiAgentConversation] = {}


# ======================
# HEALTH CHECK
# ======================

@app.get("/")
async def root():
    return {
        "service": "Volunteer Hub API",
        "version": "1.0.0",
        "status": "running",
        "features": {
            "voice": settings.ENABLE_VOICE,
            "sms": settings.ENABLE_SMS_FALLBACK,
            "digital_twins": settings.ENABLE_DIGITAL_TWINS,
            "multi_agent": settings.ENABLE_MULTI_AGENT
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ======================
# DIGITAL TWIN ENDPOINTS
# ======================

@app.post("/digital-twin/create")
async def create_digital_twin(
    request: DigitalTwinCreateRequest,
    photo: UploadFile = File(...)
):
    """
    Create a digital twin from uploaded photo and context
    Returns twin_id and initial greeting
    """
    try:
        # Save uploaded photo
        photo_path = f"/tmp/{uuid.uuid4()}_{photo.filename}"
        with open(photo_path, "wb") as f:
            content = await photo.read()
            f.write(content)

        # Generate digital twin
        generator = DigitalTwinGenerator()
        result = await generator.generate_from_photo(
            photo_path=photo_path,
            context=request.context,
            owner_id=request.owner_id
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error"))

        return {
            "twin_id": result["twin_id"],
            "entity_type": result["entity_type"],
            "initial_greeting": result["initial_greeting"],
            "personality_traits": result["personality_traits"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/digital-twin/{twin_id}")
async def get_digital_twin(twin_id: str):
    """Retrieve digital twin information"""
    # TODO: Query database for twin data
    return {
        "twin_id": twin_id,
        "status": "active"
    }


@app.post("/digital-twin/{twin_id}/converse")
async def converse_with_twin(twin_id: str, request: ConverseWithTwinRequest):
    """
    Have a conversation with a digital twin
    Twin responds in first-person as the entity
    """
    try:
        # Get or create twin agent
        if twin_id not in active_agents:
            # Load twin from database
            # TODO: Implement database loading
            system_prompt = "You are a digital twin entity."  # Placeholder
            twin_agent = DigitalTwinAgent(
                twin_id=twin_id,
                system_prompt=system_prompt
            )
            active_agents[twin_id] = twin_agent
        else:
            twin_agent = active_agents[twin_id]

        # Process message
        response = await twin_agent.converse(request.message)

        return {
            "twin_id": twin_id,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/digital-twin/{twin_id}/memories")
async def get_twin_memories(twin_id: str, memory_type: Optional[str] = None):
    """Retrieve twin's accumulated memories"""
    try:
        query_tool = QueryTwinMemoryTool()
        result = await query_tool.execute(twin_id=twin_id, memory_type=memory_type)

        if not result.success:
            raise HTTPException(status_code=404, detail=result.error)

        return {
            "twin_id": twin_id,
            "memories": result.data,
            "count": len(result.data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================
# OFFER/NEED/MATCH ENDPOINTS
# ======================

@app.post("/offers")
async def create_offer(request: CreateOfferRequest):
    """Create a new offer"""
    try:
        tool = CreateOfferTool()
        result = await tool.execute(
            person_id=request.person_id,
            item_type=request.item_type,
            quantity=request.quantity,
            unit=request.unit,
            resource_id=request.resource_id,
            available_until=request.available_until
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return {
            "offer_id": result.data["offer_id"],
            "message": result.message
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/needs")
async def find_needs(
    item_type: Optional[str] = None,
    urgency: Optional[str] = None,
    min_quantity: Optional[float] = None
):
    """Search for needs matching criteria"""
    try:
        tool = FindNeedsTool()
        result = await tool.execute(
            item_type=item_type,
            urgency=urgency,
            min_quantity=min_quantity
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        return {
            "needs": result.data,
            "count": len(result.data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/matches")
async def create_match(
    offer_id: str,
    need_id: str,
    coordinator_id: Optional[str] = None
):
    """Create a match between offer and need"""
    try:
        # Spawn coordinator agent to handle matching
        coordinator = CoordinatorAgent(
            task_description=f"Match offer {offer_id} with need {need_id}",
            offer_id=offer_id
        )

        # Execute coordination
        result = await coordinator.coordinate()

        return {
            "match_created": True,
            "coordinator_id": result["coordinator_id"],
            "result": result["result"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================
# VOICE SESSION ENDPOINTS
# ======================

@app.post("/voice/session")
async def create_voice_session(request: VoiceSessionRequest):
    """
    Create a new voice session
    Spawns Person Agent and Host Agent
    """
    try:
        session_id = str(uuid.uuid4())

        # Create person agent for this session
        person_agent = PersonAgent(
            person_id=request.person_id,
            name="User",  # TODO: Load from database
            preferences={"language": request.language}
        )

        # Create multi-agent conversation
        conversation = MultiAgentConversation(session_id=session_id)
        await conversation.add_agent(person_agent)

        # Store active conversation
        active_conversations[session_id] = conversation

        return {
            "session_id": session_id,
            "active_agents": [person_agent.agent_id],
            "language": request.language,
            "status": "active"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/voice/stream/{session_id}")
async def voice_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time voice streaming
    Handles audio in/out with Hume.ai integration
    """
    await websocket.accept()

    if session_id not in active_conversations:
        await websocket.close(code=1008, reason="Session not found")
        return

    conversation = active_conversations[session_id]

    try:
        while True:
            # Receive audio or text from client
            data = await websocket.receive_json()

            if data.get("type") == "audio":
                # TODO: Integrate Hume.ai for transcription
                text = "Placeholder transcription"
                emotions = {}
            elif data.get("type") == "text":
                text = data.get("text")
                emotions = {}
            else:
                continue

            # Process through conversation
            response = await conversation.process_user_input(text, emotions)

            # Send response back
            await websocket.send_json({
                "type": "response",
                "text": response["text"],
                "speaker": response["speaker"],
                "speaker_type": response["speaker_type"]
            })

    except WebSocketDisconnect:
        # Clean up session
        if session_id in active_conversations:
            await active_conversations[session_id].end_session()
            del active_conversations[session_id]


@app.delete("/voice/session/{session_id}")
async def end_voice_session(session_id: str):
    """End a voice session"""
    if session_id in active_conversations:
        await active_conversations[session_id].end_session()
        del active_conversations[session_id]
        return {"session_id": session_id, "status": "ended"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


# ======================
# SMS FALLBACK ENDPOINTS
# ======================

@app.post("/sms/incoming")
async def handle_incoming_sms(body: Dict[str, Any]):
    """
    Handle incoming SMS from Twilio webhook
    Provides SMS fallback for voice features
    """
    # TODO: Implement Twilio SMS handling
    from_number = body.get("From")
    message_text = body.get("Body")

    # Process message through appropriate agent
    # Return TwiML response

    return {
        "status": "processed",
        "response": "SMS handling not yet implemented"
    }


# ======================
# ADMIN/DEBUG ENDPOINTS
# ======================

@app.get("/debug/agents")
async def list_active_agents():
    """List all active agent sessions (debug)"""
    return {
        "active_agents": len(active_agents),
        "agents": [
            {
                "id": agent_id,
                "type": agent.agent_type if hasattr(agent, 'agent_type') else "unknown"
            }
            for agent_id, agent in active_agents.items()
        ]
    }


@app.get("/debug/conversations")
async def list_active_conversations():
    """List all active voice conversations (debug)"""
    return {
        "active_conversations": len(active_conversations),
        "sessions": [
            {
                "session_id": session_id,
                "agent_count": len(conv.agents) if hasattr(conv, 'agents') else 0
            }
            for session_id, conv in active_conversations.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
