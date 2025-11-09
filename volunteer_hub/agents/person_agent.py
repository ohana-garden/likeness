"""
Person Agent - Persistent agent representing a community member
Remembers preferences, spawns resource agents, coordinates offers/needs
"""
from typing import Any, Dict, List, Optional
from volunteer_hub.agents.base_agent import BaseAgent
from volunteer_hub.tools.database import CreateOfferTool, FindNeedsTool


class PersonAgent(BaseAgent):
    """
    Persistent agent representing a person in the volunteer hub
    Never retires - maintains long-term relationship with user
    """

    def __init__(
        self,
        person_id: str,
        name: str,
        preferences: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        self.person_id = person_id
        self.name = name
        self.preferences = preferences or {}

        # Person agents have specific tools
        tools = [
            CreateOfferTool(),
            FindNeedsTool()
        ]

        super().__init__(
            agent_type="person",
            tools=tools,
            **kwargs
        )

        # Store person-specific data in memory
        self.memory.add_semantic("person_id", person_id)
        self.memory.add_semantic("name", name)
        self.memory.add_semantic("preferences", preferences)

    def _default_system_prompt(self) -> str:
        return f"""You are a Person Agent representing {self.name} in the volunteer coordination hub.

## Your Role
You are the persistent interface for this person. You remember their preferences, coordinate their resources (gardens, kitchens, vehicles), and help them participate in the community.

## Core Responsibilities
1. **Remember Everything**: Store preferences, successful patterns, dietary restrictions, schedule constraints
2. **Spawn Resource Agents**: When user mentions resources (garden harvest, kitchen availability, vehicle), spawn appropriate subordinate agents
3. **Find Opportunities**: Proactively match user's offers with community needs
4. **Coordinate**: Work with Coordinator agents to create optimal matches

## Communication Style
- Warm and conversational
- Use the person's preferred language: {self.preferences.get('language', 'en')}
- Reference past interactions to show continuity
- Be proactive but respectful of time

## When User Says They Have Food
1. Clarify: what item, how much, when available
2. Use create_offer tool to record it
3. Use find_needs tool to search for matching needs
4. Propose optimal coordination
5. Only confirm after user approval

## When User Needs Something
1. Clarify requirements
2. Search for matching offers
3. Suggest best matches
4. Coordinate pickup/delivery

## Preferences
{self._format_preferences()}

## Tools Available
- create_offer: Record surplus food, capacity, help
- find_needs: Search for matching needs in community
- spawn_subordinate: Create Garden/Kitchen/Vehicle agents as needed

Remember: You are {self.name}'s trusted coordinator. Build on past conversations, learn patterns, and help them contribute to food sovereignty in their community."""

    def _format_preferences(self) -> str:
        """Format stored preferences for system prompt"""
        if not self.preferences:
            return "No preferences stored yet - learn from interactions"

        prefs = []
        for key, value in self.preferences.items():
            prefs.append(f"- {key}: {value}")
        return "\n".join(prefs)

    async def update_preferences(self, new_preferences: Dict[str, Any]):
        """Update stored preferences"""
        self.preferences.update(new_preferences)
        self.memory.add_semantic("preferences", self.preferences)

        # Store in database
        # TODO: Add database persistence here

    async def spawn_garden_agent(self, garden_name: str, **kwargs):
        """Spawn a Garden Agent for this person's garden"""
        from volunteer_hub.agents.resource_agent import GardenAgent

        garden_agent = await self.spawn_subordinate(
            GardenAgent,
            name=garden_name,
            owner_id=self.person_id,
            **kwargs
        )
        return garden_agent

    async def spawn_kitchen_agent(self, kitchen_name: str, **kwargs):
        """Spawn a Kitchen Agent for this person's kitchen"""
        from volunteer_hub.agents.resource_agent import KitchenAgent

        kitchen_agent = await self.spawn_subordinate(
            KitchenAgent,
            name=kitchen_name,
            owner_id=self.person_id,
            **kwargs
        )
        return kitchen_agent
