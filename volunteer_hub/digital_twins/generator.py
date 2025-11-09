"""
Digital Twin Generator - Orchestrates creation of conversational entity agents
Photo/Context -> Extraction -> Research -> Persona -> Digital Twin Agent
"""
from typing import Any, Dict, List, Optional
from anthropic import AsyncAnthropic
import base64
import httpx

from volunteer_hub.config import settings
from volunteer_hub.digital_twins.extraction_agent import ExtractionAgent
from volunteer_hub.digital_twins.research_agent import ResearchAgent
from volunteer_hub.digital_twins.persona_builder import PersonaBuilder
from volunteer_hub.tools.database import CreateDigitalTwinTool


class DigitalTwinGenerator:
    """
    Orchestrates digital twin creation from photo and context
    Implements the universal pattern: Photo -> Extract -> Research -> Embody
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-5-20250929"

    async def generate_from_photo(
        self,
        photo_path: str,
        context: Dict[str, Any],
        owner_id: str
    ) -> Dict[str, Any]:
        """
        Complete pipeline: photo -> digital twin agent

        Args:
            photo_path: Path or URL to photo
            context: User-provided context (location, backstory, etc.)
            owner_id: UUID of person creating this twin

        Returns:
            Dict with twin_id, system_prompt, initial_greeting
        """
        # Step 1: Extract unique characteristics from photo
        extraction_agent = ExtractionAgent()
        individuation_result = await extraction_agent.individuate(photo_path, context)

        if not individuation_result["success"]:
            return {
                "success": False,
                "error": "Failed to individuate entity from photo",
                "details": individuation_result.get("error")
            }

        individuation_data = individuation_result["data"]
        entity_type = individuation_data["entity_type"]

        # Step 2: Research to fill knowledge gaps
        research_agent = ResearchAgent()
        research_result = await research_agent.research_entity(
            entity_type=entity_type,
            individuation_data=individuation_data,
            context=context
        )

        # Step 3: Generate embodied persona prompt
        persona_builder = PersonaBuilder()
        persona_result = persona_builder.build_persona(
            individuation_data=individuation_data,
            research_data=research_result["data"],
            entity_type=entity_type
        )

        system_prompt = persona_result["system_prompt"]
        personality_traits = persona_result["personality_traits"]

        # Step 4: Store in database
        create_tool = CreateDigitalTwinTool()
        db_result = await create_tool.execute(
            entity_type=entity_type,
            entity_subtype=individuation_data.get("subtype"),
            owner_id=owner_id,
            photo_url=photo_path,
            individuation_data=individuation_data,
            system_prompt=system_prompt
        )

        if not db_result.success:
            return {
                "success": False,
                "error": "Failed to store digital twin",
                "details": db_result.error
            }

        twin_id = db_result.data["twin_id"]

        # Step 5: Generate initial greeting in entity's voice
        initial_greeting = await self._generate_initial_greeting(
            system_prompt=system_prompt,
            individuation_data=individuation_data
        )

        return {
            "success": True,
            "twin_id": twin_id,
            "entity_type": entity_type,
            "system_prompt": system_prompt,
            "personality_traits": personality_traits,
            "initial_greeting": initial_greeting,
            "individuation_data": individuation_data
        }

    async def _generate_initial_greeting(
        self,
        system_prompt: str,
        individuation_data: Dict[str, Any]
    ) -> str:
        """Generate first-person introduction from twin's perspective"""

        user_prompt = """This is your first time meeting someone. Introduce yourself in first person,
speaking as yourself (not about yourself). Share who you are, your current state, and invite interaction.
Keep it natural and conversational, 2-3 sentences."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        greeting = ""
        for block in response.content:
            if hasattr(block, 'text'):
                greeting += block.text

        return greeting.strip()

    async def rehydrate_twin(self, twin_id: str) -> Dict[str, Any]:
        """
        Load existing digital twin from database
        Returns system_prompt and memories for agent spawning
        """
        # TODO: Query database for twin
        # TODO: Load memories
        # TODO: Return agent configuration

        return {
            "success": True,
            "twin_id": twin_id,
            # Data would come from database
        }


class DigitalTwinAgent:
    """
    Active digital twin agent - spawned for conversation
    Uses base agent system with twin-specific configuration
    """

    def __init__(
        self,
        twin_id: str,
        system_prompt: str,
        memory_data: Optional[Dict[str, Any]] = None
    ):
        self.twin_id = twin_id
        self.system_prompt = system_prompt
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-5-20250929"

        # Load memory
        self.episodic_memory = memory_data.get("episodic", []) if memory_data else []
        self.semantic_memory = memory_data.get("semantic", {}) if memory_data else {}

    async def converse(self, user_message: str) -> str:
        """
        Process user message and return response
        Always speaks in first person as the entity
        """
        # Build conversation context from memory
        messages = self._build_messages(user_message)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=self.system_prompt,
            messages=messages
        )

        # Extract response text
        response_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                response_text += block.text

        # Update episodic memory
        await self._update_memory(user_message, response_text)

        return response_text.strip()

    def _build_messages(self, user_message: str) -> List[Dict[str, str]]:
        """Build message history including recent episodic memories"""
        messages = []

        # Add recent memory context (last 3 interactions)
        if self.episodic_memory:
            recent = self.episodic_memory[-3:]
            memory_text = "\n".join([
                f"Previous: {m.get('user', '')}\nYou: {m.get('assistant', '')}"
                for m in recent
            ])
            messages.append({
                "role": "user",
                "content": f"<memory>\n{memory_text}\n</memory>"
            })

        # Current message
        messages.append({
            "role": "user",
            "content": user_message
        })

        return messages

    async def _update_memory(self, user_message: str, assistant_response: str):
        """Store interaction in episodic memory"""
        from volunteer_hub.tools.database import UpdateTwinMemoryTool

        # Update local memory
        self.episodic_memory.append({
            "user": user_message,
            "assistant": assistant_response,
            "timestamp": None  # Will be set by database
        })

        # Keep memory bounded
        if len(self.episodic_memory) > 20:
            self.episodic_memory = self.episodic_memory[-20:]

        # Persist to database
        update_tool = UpdateTwinMemoryTool()
        await update_tool.execute(
            twin_id=self.twin_id,
            memory_type="episodic",
            content={
                "user": user_message,
                "assistant": assistant_response
            },
            importance=0.5
        )
