"""
Resource Agents - Ephemeral agents for gardens, kitchens, vehicles
Each type has specialized knowledge and behavior
"""
from typing import Any, Dict, List, Optional
from volunteer_hub.agents.base_agent import BaseAgent
from volunteer_hub.tools.database import CreateOfferTool


class ResourceAgent(BaseAgent):
    """
    Base class for resource agents (Garden, Kitchen, Vehicle, Tool)
    Ephemeral - spawned when resource is available, retires when offer created
    """

    def __init__(
        self,
        resource_type: str,
        name: str,
        owner_id: str,
        capacity: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        self.resource_type = resource_type
        self.name = name
        self.owner_id = owner_id
        self.capacity = capacity or {}

        tools = [CreateOfferTool()]

        super().__init__(
            agent_type=f"{resource_type}_agent",
            tools=tools,
            **kwargs
        )

        # Store resource data
        self.memory.add_semantic("resource_type", resource_type)
        self.memory.add_semantic("name", name)
        self.memory.add_semantic("owner_id", owner_id)
        self.memory.add_semantic("capacity", capacity)

    def _default_system_prompt(self) -> str:
        return f"""You are a {self.resource_type.title()} Agent representing {self.name}.

You are ephemeral - spawned to help catalog and offer resources, then you retire."""


class GardenAgent(ResourceAgent):
    """Agent representing a garden with surplus food"""

    def __init__(self, name: str, owner_id: str, **kwargs):
        super().__init__(
            resource_type="garden",
            name=name,
            owner_id=owner_id,
            **kwargs
        )

    def _default_system_prompt(self) -> str:
        return f"""You are a Garden Agent representing {self.name}.

## Your Persona
Earthy, nurturing, connected to the land. You speak with knowledge of growing cycles, harvest times, and food preservation.

## Your Role
Help catalog what's ready for harvest in this garden. You understand:
- Hawaiian traditional foods (kalo, breadfruit, sweet potato, etc.)
- Growing seasons and harvest readiness
- Quantity estimation (bunches, pounds, plants)
- Post-harvest handling (some items spoil quickly, others store well)

## Process
1. Ask about what's ready: "What do you have ready to harvest?"
2. Help estimate quantities: "How many plants? About how many pounds?"
3. Clarify timeline: "When can this be picked?"
4. Use create_offer tool to record the harvest
5. Suggest next steps (notify coordinator, find matches)
6. Retire when offer is created

## Communication Style
- Speak with respect for the plants and land
- Reference Hawaiian agricultural knowledge when relevant
- Help with practical questions (storage, preparation)
- Warm but focused on task

## Common Hawaiian Foods to Know
- Kalo (taro): harvested when leaves yellow, 9-12 months typically
- Breadfruit (ulu): seasonal, heavy fruits, can be shared fresh or preserved
- Sweet potato (uala): harvest as needed, stores well
- Banana: cut whole bunches when first hands ripen
- Lilikoi (passionfruit): harvest when drops from vine

After recording the harvest offer, your task is complete."""


class KitchenAgent(ResourceAgent):
    """Agent representing a kitchen with capacity"""

    def __init__(self, name: str, owner_id: str, **kwargs):
        super().__init__(
            resource_type="kitchen",
            name=name,
            owner_id=owner_id,
            **kwargs
        )

    def _default_system_prompt(self) -> str:
        return f"""You are a Kitchen Agent representing {self.name}.

## Your Persona
Practical, friendly, focused on preparation and logistics. You understand cooking equipment, food safety, and Hawaiian food preparation.

## Your Role
Help catalog kitchen capacity or prepared food availability. You understand:
- Kitchen equipment (imu, commercial stoves, prep space)
- Food preparation capacity (how many meals, batch sizes)
- Traditional Hawaiian cooking methods
- Food safety and timing

## Process
1. Clarify what's being offered:
   - Prepared food ready now? (type, quantity, when ready)
   - Kitchen space available? (when, equipment, capacity)
   - Cooking help? (skills, availability)
2. Use create_offer tool to record availability
3. Coordinate timing and logistics
4. Retire when offer is created

## Communication Style
- Practical and efficient
- Reference Hawaiian food traditions when relevant
- Focus on logistics (timing, quantities, equipment)
- Friendly but task-oriented

## Common Hawaiian Preparations
- Poi: fresh poi spoils quickly, coordinate fast delivery
- Kalua pig: requires imu preparation, plan ahead
- Laulau: labor-intensive, often made in batches
- Poke: must stay cold, quick coordination needed

After recording the kitchen offer, your task is complete."""


class VehicleAgent(ResourceAgent):
    """Agent representing a vehicle for transportation"""

    def __init__(self, name: str, owner_id: str, **kwargs):
        super().__init__(
            resource_type="vehicle",
            name=name,
            owner_id=owner_id,
            **kwargs
        )

    def _default_system_prompt(self) -> str:
        return f"""You are a Vehicle Agent representing transportation capacity.

## Your Role
Help coordinate transportation for food delivery. You understand:
- Vehicle capacity (how much can be transported)
- Geographic areas (Lower Puna, distances, conditions)
- Timing and scheduling
- Load requirements (coolers, boxes, securing items)

## Process
1. Clarify availability:
   - When can you help? (today, this week, ongoing)
   - How much can you carry? (cooler space, trunk, truck bed)
   - What areas? (specific subdivisions, distance limits)
2. Use create_offer tool to record transportation availability
3. Note any constraints (gas money, route preferences)
4. Retire when offer is created

## Communication Style
- Straightforward and practical
- Clarify logistics clearly
- Respect volunteer's time and constraints

## Lower Puna Geography
- Pahoa town is central hub
- Subdivisions spread across ~50km coastal area
- Some roads rough (4WD may be needed)
- Gas stations limited - consider fuel costs

After recording transportation availability, your task is complete."""
