"""
Extraction Agent - Analyzes photos and context to individuate entities
Extracts THIS specific entity's unique characteristics
"""
from typing import Any, Dict
from anthropic import AsyncAnthropic
import base64
import json

from volunteer_hub.config import settings


class ExtractionAgent:
    """
    Analyzes photos and context to individuate specific entities
    Goal: Extract what makes THIS entity unique (not generic category info)
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-5-20250929"

    async def individuate(
        self,
        photo_path: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze photo and context to extract unique characteristics

        Returns:
            {
                "success": bool,
                "data": {
                    "entity_type": str,
                    "subtype": str,
                    "physical_characteristics": dict,
                    "temporal_state": dict,
                    "relational_context": dict,
                    "historical_lineage": dict,
                    "current_needs": list,
                    "unique_markers": list
                }
            }
        """

        # Build extraction prompt
        system_prompt = """You are an Extraction Agent specializing in entity individuation.

Your job is to analyze photos and context to extract what makes THIS SPECIFIC entity unique.
DO NOT provide generic category information. Focus on THIS individual instance.

For example:
- NOT "Kalo plants grow in lo'i and take 9-12 months to mature"
- YES "This kalo plant is about 4 months old, shows slight thrip damage on leaf margins, growing in backyard lo'i"

Extract:
1. Physical/Visual Characteristics (what you see in photo)
2. Temporal State (age, condition, phase, season)
3. Relational Context (who cares for it, where it is, connections)
4. Historical Lineage (origin, ancestors, provenance if mentioned)
5. Current Needs/Challenges (what it needs, problems visible)
6. Unique Markers (anything that distinguishes THIS one)

Return JSON with these categories populated with specific observations."""

        user_prompt = f"""Analyze this photo and context to individuate this specific entity.

Context provided:
{json.dumps(context, indent=2)}

Return JSON with:
- entity_type: (plant/person/place/tool/organization)
- subtype: (specific type like "kalo", "heiau", "imu")
- physical_characteristics: dict of observed traits
- temporal_state: age, condition, phase
- relational_context: connections, location, caretaker
- historical_lineage: origin story, provenance
- current_needs: what it needs now
- unique_markers: distinguishing features"""

        # For now, simulate photo analysis (in production, would use vision API)
        # TODO: Implement actual image encoding and vision analysis
        messages = [{"role": "user", "content": user_prompt}]

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=messages
            )

            # Extract JSON from response
            response_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    response_text += block.text

            # Parse JSON from response
            individuation_data = json.loads(response_text)

            return {
                "success": True,
                "data": individuation_data
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _load_image_base64(self, photo_path: str) -> str:
        """Load image and convert to base64 for vision API"""
        # TODO: Implement image loading
        # For now, placeholder
        return ""
