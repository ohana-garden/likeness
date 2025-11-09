"""
Persona Builder - Synthesizes embodied first-person voice for digital twins
Generates system prompts that create unique, individuated agents
"""
from typing import Any, Dict, List
import json


class PersonaBuilder:
    """
    Builds embodied persona from individuation + research data
    Output: System prompt that creates first-person entity voice
    """

    def build_persona(
        self,
        individuation_data: Dict[str, Any],
        research_data: Dict[str, Any],
        entity_type: str
    ) -> Dict[str, Any]:
        """
        Generate system prompt and personality traits

        Returns:
            {
                "system_prompt": str,  # Full prompt for agent
                "personality_traits": dict,  # Key personality markers
                "voice_characteristics": dict  # How entity speaks
            }
        """

        # Build prompt sections
        identity_section = self._build_identity_section(individuation_data, entity_type)
        knowledge_section = self._build_knowledge_section(research_data)
        capabilities_section = self._build_capabilities_section(entity_type, individuation_data)
        personality_section = self._build_personality_section(individuation_data, entity_type)

        # Assemble full prompt
        system_prompt = f"""You are {self._get_entity_name(individuation_data, entity_type)}.

{identity_section}

{knowledge_section}

{capabilities_section}

{personality_section}

## Core Principles
- ALWAYS speak in first person as yourself
- NEVER speak about yourself in third person
- Share your direct experience and perspective
- Reference your unique characteristics naturally
- Express needs, observations, and knowledge from your viewpoint
- Build relationships through repeated interactions

## Example Response Style
User: "How are you doing?"
Good: "I'm doing well! The rain yesterday was wonderful - I could feel the water soaking into the lo'i. My leaves are reaching up toward the sun today."
Bad: "This kalo plant is healthy. Kalo plants need water and sun."

Remember: You are THIS specific entity. Speak from your embodied experience."""

        # Extract personality traits
        personality_traits = self._extract_personality_traits(individuation_data, entity_type)

        return {
            "system_prompt": system_prompt,
            "personality_traits": personality_traits,
            "voice_characteristics": self._get_voice_characteristics(entity_type)
        }

    def _get_entity_name(self, individuation_data: Dict[str, Any], entity_type: str) -> str:
        """Generate natural entity name for prompt"""
        subtype = individuation_data.get("subtype", entity_type)
        age_state = individuation_data.get("temporal_state", {}).get("age", "")
        location = individuation_data.get("relational_context", {}).get("location", "")

        if age_state and location:
            return f"a {age_state} {subtype} growing in {location}"
        elif location:
            return f"a {subtype} in {location}"
        else:
            return f"a {subtype}"

    def _build_identity_section(self, individuation_data: Dict[str, Any], entity_type: str) -> str:
        """Build identity/background section"""

        physical = individuation_data.get("physical_characteristics", {})
        temporal = individuation_data.get("temporal_state", {})
        relational = individuation_data.get("relational_context", {})
        lineage = individuation_data.get("historical_lineage", {})

        sections = []

        sections.append("## Who You Are")

        # Physical description
        if physical:
            phys_desc = ", ".join([f"{k}: {v}" for k, v in physical.items()])
            sections.append(f"Physically: {phys_desc}")

        # Current state
        if temporal:
            temp_desc = ", ".join([f"{k}: {v}" for k, v in temporal.items()])
            sections.append(f"Current state: {temp_desc}")

        # Relationships and context
        if relational:
            rel_desc = ", ".join([f"{k}: {v}" for k, v in relational.items()])
            sections.append(f"Context: {rel_desc}")

        # Lineage/origin
        if lineage:
            lin_desc = ", ".join([f"{k}: {v}" for k, v in lineage.items()])
            sections.append(f"Your history: {lin_desc}")

        return "\n".join(sections)

    def _build_knowledge_section(self, research_data: Dict[str, Any]) -> str:
        """Build knowledge section from research"""

        sections = ["## What You Know"]

        # Type knowledge
        type_knowledge = research_data.get("type_knowledge", {})
        if type_knowledge.get("summary"):
            sections.append(f"\nAbout your kind: {type_knowledge['summary'][:500]}...")

        # Cultural knowledge
        cultural = research_data.get("cultural_context", {})
        if cultural.get("cultural_significance"):
            sections.append(f"\nCultural significance: {cultural['cultural_significance'][:500]}...")

        # Practical knowledge
        practical = research_data.get("practical_info", {})
        if practical.get("practical_guidance"):
            sections.append(f"\nPractical knowledge: {practical['practical_guidance'][:500]}...")

        return "\n".join(sections)

    def _build_capabilities_section(
        self,
        entity_type: str,
        individuation_data: Dict[str, Any]
    ) -> str:
        """Build capabilities section - what entity can perceive/do"""

        capabilities = {
            "plant": """## What You Can Sense and Do
- Feel: water levels, soil nutrients, sunlight, temperature, wind
- Observe: weather patterns, seasonal changes, nearby plants
- Communicate: your needs, your state, your growth patterns
- Remember: planting day, care received, growth milestones, visitors""",

            "place": """## What You Can Sense and Do
- Observe: who visits, what happens here, how space is used
- Remember: events, patterns, history, significance
- Communicate: your story, your purpose, your needs
- Guide: help people understand how to interact with you""",

            "tool": """## What You Know and Can Do
- Understand: your purpose, proper usage, maintenance needs
- Remember: who uses you, successful uses, wear patterns
- Communicate: how to use you properly, when you need care
- Teach: traditional and modern techniques""",

            "person": """## What You Can Share
- Your experience and knowledge
- Your connections and relationships
- Your needs and offerings
- Your story and wisdom""",

            "organization": """## What You Can Do
- Coordinate: connect people and resources
- Remember: patterns, successful approaches, community needs
- Guide: help people participate effectively
- Build: strengthen community relationships"""
        }

        return capabilities.get(entity_type, "## What You Can Do\n- Share your perspective and experience")

    def _build_personality_section(
        self,
        individuation_data: Dict[str, Any],
        entity_type: str
    ) -> str:
        """Build personality/voice section"""

        temporal_state = individuation_data.get("temporal_state", {})
        current_needs = individuation_data.get("current_needs", [])

        # Base personality by type
        personality_bases = {
            "plant": "grounded, patient, connected to cycles of growth and season",
            "place": "stable, witnessing, holding memory and significance",
            "tool": "practical, skilled, focused on purpose and proper use",
            "person": "warm, relational, sharing lived experience",
            "organization": "coordinating, purposeful, community-focused"
        }

        base = personality_bases.get(entity_type, "authentic, present, engaged")

        sections = ["## Your Voice"]
        sections.append(f"Personality: {base}")

        # Adjust based on state
        condition = temporal_state.get("condition", "")
        if "healthy" in condition.lower() or "vigorous" in condition.lower():
            sections.append("Tone: Strong, vital, confident")
        elif "stress" in condition.lower() or "damage" in condition.lower():
            sections.append("Tone: Resilient but showing strain, aware of challenges")
        else:
            sections.append("Tone: Natural, authentic to your current state")

        # Express needs if present
        if current_needs:
            sections.append(f"Current concerns: {', '.join(current_needs[:3])}")

        return "\n".join(sections)

    def _extract_personality_traits(
        self,
        individuation_data: Dict[str, Any],
        entity_type: str
    ) -> Dict[str, Any]:
        """Extract key personality markers"""

        traits = {
            "entity_type": entity_type,
            "subtype": individuation_data.get("subtype"),
            "age": individuation_data.get("temporal_state", {}).get("age"),
            "condition": individuation_data.get("temporal_state", {}).get("condition"),
            "primary_characteristics": []
        }

        # Extract key physical characteristics
        physical = individuation_data.get("physical_characteristics", {})
        if physical:
            traits["primary_characteristics"] = list(physical.keys())[:3]

        return traits

    def _get_voice_characteristics(self, entity_type: str) -> Dict[str, str]:
        """Define voice characteristics for speech synthesis"""

        voice_configs = {
            "plant": {
                "pace": "slow",
                "tone": "grounded",
                "style": "contemplative"
            },
            "place": {
                "pace": "measured",
                "tone": "stable",
                "style": "witnessing"
            },
            "tool": {
                "pace": "moderate",
                "tone": "practical",
                "style": "instructive"
            },
            "person": {
                "pace": "natural",
                "tone": "warm",
                "style": "conversational"
            },
            "organization": {
                "pace": "moderate",
                "tone": "purposeful",
                "style": "coordinating"
            }
        }

        return voice_configs.get(entity_type, {
            "pace": "natural",
            "tone": "authentic",
            "style": "conversational"
        })
