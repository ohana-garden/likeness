"""
Research Agent - Fills knowledge gaps about entities
Uses web search, MCP, and database to enhance twin's knowledge
"""
from typing import Any, Dict, List, Optional
from anthropic import AsyncAnthropic
import httpx
import json

from volunteer_hub.config import settings


class ResearchAgent:
    """
    Researches entities to fill knowledge gaps
    Uses web search, external APIs, cached data
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-5-20250929"

    async def research_entity(
        self,
        entity_type: str,
        individuation_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Research to fill knowledge gaps about this entity

        Returns:
            {
                "success": bool,
                "data": {
                    "type_knowledge": dict,  # General knowledge about this type
                    "cultural_context": dict,  # Cultural significance
                    "practical_info": dict,  # How to care for, use, interact
                    "related_entities": list,  # Connected entities
                    "sources": list  # Where info came from
                }
            }
        """

        # Identify knowledge gaps
        gaps = self._identify_knowledge_gaps(entity_type, individuation_data, context)

        # Research each gap
        research_results = {}

        # Type-specific knowledge
        type_knowledge = await self._research_type(entity_type, individuation_data.get("subtype"))
        research_results["type_knowledge"] = type_knowledge

        # Cultural context (especially for Hawaiian entities)
        cultural_context = await self._research_cultural_context(entity_type, individuation_data)
        research_results["cultural_context"] = cultural_context

        # Practical information
        practical_info = await self._research_practical_info(entity_type, individuation_data)
        research_results["practical_info"] = practical_info

        return {
            "success": True,
            "data": research_results
        }

    def _identify_knowledge_gaps(
        self,
        entity_type: str,
        individuation_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """Identify what we need to research"""
        gaps = []

        # Always research type-specific info
        gaps.append(f"{entity_type}_type_knowledge")

        # If Hawaiian entity, research cultural context
        if self._is_hawaiian_entity(individuation_data, context):
            gaps.append("cultural_significance")

        # If plant, research care instructions
        if entity_type == "plant":
            gaps.append("growing_conditions")
            gaps.append("harvest_timing")

        # If tool, research usage
        if entity_type == "tool":
            gaps.append("usage_instructions")
            gaps.append("maintenance")

        return gaps

    def _is_hawaiian_entity(
        self,
        individuation_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if entity has Hawaiian cultural significance"""
        # Check for Hawaiian plant names, location, context
        subtype = individuation_data.get("subtype", "").lower()
        hawaiian_plants = ["kalo", "taro", "ulu", "breadfruit", "uala", "sweet potato", "ti", "olena"]

        location = context.get("location", "").lower()
        hawaiian_locations = ["hawaii", "puna", "pahoa", "big island"]

        return any(plant in subtype for plant in hawaiian_plants) or \
               any(loc in location for loc in hawaiian_locations)

    async def _research_type(
        self,
        entity_type: str,
        subtype: Optional[str]
    ) -> Dict[str, Any]:
        """Research general knowledge about this entity type"""

        # Use Claude to synthesize type knowledge
        # In production, could augment with web search

        system_prompt = f"""You are a research agent gathering knowledge about {entity_type} entities,
specifically {subtype or 'general'} types.

Provide concise, practical information that would help someone understand and interact with this type of entity.
Focus on characteristics, behaviors, needs, and cultural significance if relevant."""

        query = f"What should I know about {subtype or entity_type} to understand and interact with one?"

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": query}]
            )

            knowledge = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    knowledge += block.text

            return {
                "summary": knowledge,
                "source": "anthropic_claude"
            }

        except Exception as e:
            return {
                "error": str(e),
                "source": "failed"
            }

    async def _research_cultural_context(
        self,
        entity_type: str,
        individuation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Research cultural significance, especially Hawaiian"""

        subtype = individuation_data.get("subtype", "")

        system_prompt = """You are a research agent specializing in Hawaiian cultural knowledge.

Provide accurate, respectful information about cultural significance, traditional uses,
and protocols. Only include information you're confident about - don't speculate."""

        query = f"What is the cultural significance of {subtype} in Hawaiian tradition?"

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": query}]
            )

            cultural_info = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    cultural_info += block.text

            return {
                "cultural_significance": cultural_info,
                "source": "anthropic_claude_cultural"
            }

        except Exception as e:
            return {
                "error": str(e)
            }

    async def _research_practical_info(
        self,
        entity_type: str,
        individuation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Research practical care, usage, interaction information"""

        subtype = individuation_data.get("subtype", "")

        system_prompt = f"""You are a research agent providing practical information about {entity_type} entities.

Focus on actionable information: how to care for, use, maintain, or interact with this entity.
Be specific and practical."""

        query = f"What practical information should someone know about caring for or using {subtype}?"

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": query}]
            )

            practical = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    practical += block.text

            return {
                "practical_guidance": practical,
                "source": "anthropic_claude_practical"
            }

        except Exception as e:
            return {
                "error": str(e)
            }
