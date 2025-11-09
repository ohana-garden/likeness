"""
Database Tools - Operations for offers, needs, matches, and digital twins
"""
from typing import Any, Dict, List, Optional
import asyncpg
from datetime import datetime
import hashlib
import json

from volunteer_hub.tools.base_tool import BaseTool, ToolResponse
from volunteer_hub.config import settings


class DatabaseConnection:
    """Shared database connection pool"""
    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(settings.async_database_url)
        return cls._pool

    @classmethod
    async def close(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None


# ======================
# OFFER TOOLS
# ======================

class CreateOfferTool(BaseTool):
    """Create a new offer (surplus food, capacity, help)"""

    def __init__(self):
        super().__init__(
            name="create_offer",
            description="Create a new offer of food, space, or help from a person or resource"
        )

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "person_id": {
                "type": "string",
                "description": "UUID of the person making the offer",
                "required": True
            },
            "item_type": {
                "type": "string",
                "description": "Type of item being offered (e.g., 'kalo', 'breadfruit', 'kitchen_space')",
                "required": True
            },
            "quantity": {
                "type": "number",
                "description": "Amount available",
                "required": True
            },
            "unit": {
                "type": "string",
                "description": "Unit of measurement (default: lbs)",
                "required": False
            },
            "resource_id": {
                "type": "string",
                "description": "UUID of associated resource (garden, kitchen, etc.)",
                "required": False
            },
            "available_until": {
                "type": "string",
                "description": "ISO timestamp when offer expires",
                "required": False
            }
        }

    async def execute(
        self,
        person_id: str,
        item_type: str,
        quantity: float,
        unit: str = "lbs",
        resource_id: Optional[str] = None,
        available_until: Optional[str] = None
    ) -> ToolResponse:
        try:
            pool = await DatabaseConnection.get_pool()
            async with pool.acquire() as conn:
                offer_id = await conn.fetchval(
                    """
                    INSERT INTO offers (person_id, resource_id, item_type, quantity, unit, available_until)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                    """,
                    person_id, resource_id, item_type, quantity, unit, available_until
                )
                return ToolResponse(
                    success=True,
                    message=f"Offer created: {quantity} {unit} of {item_type}",
                    data={"offer_id": str(offer_id)}
                )
        except Exception as e:
            return ToolResponse(success=False, message="Failed to create offer", error=str(e))


class FindNeedsTool(BaseTool):
    """Find needs that match available offers"""

    def __init__(self):
        super().__init__(
            name="find_needs",
            description="Search for needs that match an offer or criteria"
        )

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "item_type": {
                "type": "string",
                "description": "Type of item needed",
                "required": False
            },
            "urgency": {
                "type": "string",
                "description": "Filter by urgency level (immediate, today, this_week, normal)",
                "required": False
            },
            "min_quantity": {
                "type": "number",
                "description": "Minimum quantity needed",
                "required": False
            }
        }

    async def execute(
        self,
        item_type: Optional[str] = None,
        urgency: Optional[str] = None,
        min_quantity: Optional[float] = None
    ) -> ToolResponse:
        try:
            pool = await DatabaseConnection.get_pool()
            async with pool.acquire() as conn:
                query = "SELECT id, program_id, item_type, quantity, unit, urgency, dietary_restrictions FROM needs WHERE status = 'open'"
                params = []

                if item_type:
                    params.append(item_type)
                    query += f" AND item_type ILIKE '%' || ${len(params)} || '%'"

                if urgency:
                    params.append(urgency)
                    query += f" AND urgency = ${len(params)}"

                if min_quantity:
                    params.append(min_quantity)
                    query += f" AND quantity >= ${len(params)}"

                query += " ORDER BY urgency DESC, created_at ASC LIMIT 20"

                needs = await conn.fetch(query, *params)
                needs_list = [dict(n) for n in needs]

                return ToolResponse(
                    success=True,
                    message=f"Found {len(needs_list)} matching needs",
                    data=needs_list
                )
        except Exception as e:
            return ToolResponse(success=False, message="Failed to find needs", error=str(e))


class CreateMatchTool(BaseTool):
    """Create a match between an offer and a need"""

    def __init__(self):
        super().__init__(
            name="create_match",
            description="Coordinate an offer with a need, creating a match"
        )

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "offer_id": {
                "type": "string",
                "description": "UUID of the offer",
                "required": True
            },
            "need_id": {
                "type": "string",
                "description": "UUID of the need",
                "required": True
            },
            "coordinator_agent_id": {
                "type": "string",
                "description": "ID of the coordinator agent making the match",
                "required": True
            },
            "pickup_time": {
                "type": "string",
                "description": "ISO timestamp for pickup",
                "required": False
            },
            "delivery_time": {
                "type": "string",
                "description": "ISO timestamp for delivery",
                "required": False
            }
        }

    async def execute(
        self,
        offer_id: str,
        need_id: str,
        coordinator_agent_id: str,
        pickup_time: Optional[str] = None,
        delivery_time: Optional[str] = None
    ) -> ToolResponse:
        try:
            pool = await DatabaseConnection.get_pool()
            async with pool.acquire() as conn:
                # Create match
                match_id = await conn.fetchval(
                    """
                    INSERT INTO matches (offer_id, need_id, coordinator_agent_id, pickup_time, delivery_time)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                    """,
                    offer_id, need_id, coordinator_agent_id, pickup_time, delivery_time
                )

                # Update offer and need status
                await conn.execute(
                    "UPDATE offers SET status = 'matched' WHERE id = $1",
                    offer_id
                )
                await conn.execute(
                    "UPDATE needs SET status = 'matched' WHERE id = $1",
                    need_id
                )

                return ToolResponse(
                    success=True,
                    message="Match created successfully",
                    data={"match_id": str(match_id)}
                )
        except Exception as e:
            return ToolResponse(success=False, message="Failed to create match", error=str(e))


# ======================
# DIGITAL TWIN TOOLS
# ======================

class CreateDigitalTwinTool(BaseTool):
    """Create a new digital twin from photo and context"""

    def __init__(self):
        super().__init__(
            name="create_digital_twin",
            description="Create a digital twin entity from photo analysis and context"
        )

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "entity_type": {
                "type": "string",
                "description": "Type of entity (plant, person, place, tool, organization)",
                "required": True
            },
            "entity_subtype": {
                "type": "string",
                "description": "Specific subtype (e.g., 'kalo', 'heiau')",
                "required": False
            },
            "owner_id": {
                "type": "string",
                "description": "UUID of person who created this twin",
                "required": True
            },
            "photo_url": {
                "type": "string",
                "description": "URL or path to photo",
                "required": False
            },
            "individuation_data": {
                "type": "object",
                "description": "Extracted unique characteristics of this entity",
                "required": True
            },
            "system_prompt": {
                "type": "string",
                "description": "Generated embodiment instructions",
                "required": True
            },
            "parent_id": {
                "type": "string",
                "description": "Parent twin ID for hierarchies",
                "required": False
            }
        }

    async def execute(
        self,
        entity_type: str,
        owner_id: str,
        individuation_data: Dict[str, Any],
        system_prompt: str,
        entity_subtype: Optional[str] = None,
        photo_url: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> ToolResponse:
        try:
            # Generate photo hash for deduplication
            photo_hash = None
            if photo_url:
                photo_hash = hashlib.sha256(photo_url.encode()).hexdigest()

            pool = await DatabaseConnection.get_pool()
            async with pool.acquire() as conn:
                twin_id = await conn.fetchval(
                    """
                    INSERT INTO digital_twins
                    (entity_type, entity_subtype, parent_id, owner_id, photo_hash, photo_url,
                     individuation_data, system_prompt)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                    """,
                    entity_type, entity_subtype, parent_id, owner_id, photo_hash, photo_url,
                    json.dumps(individuation_data), system_prompt
                )

                return ToolResponse(
                    success=True,
                    message=f"Digital twin created: {entity_type}",
                    data={"twin_id": str(twin_id)}
                )
        except Exception as e:
            return ToolResponse(success=False, message="Failed to create digital twin", error=str(e))


class QueryTwinMemoryTool(BaseTool):
    """Retrieve a digital twin's memories"""

    def __init__(self):
        super().__init__(
            name="query_twin_memory",
            description="Retrieve memories for a digital twin"
        )

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "twin_id": {
                "type": "string",
                "description": "UUID of the digital twin",
                "required": True
            },
            "memory_type": {
                "type": "string",
                "description": "Filter by memory type (episodic, semantic, procedural)",
                "required": False
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of memories to return",
                "required": False
            }
        }

    async def execute(
        self,
        twin_id: str,
        memory_type: Optional[str] = None,
        limit: int = 20
    ) -> ToolResponse:
        try:
            pool = await DatabaseConnection.get_pool()
            async with pool.acquire() as conn:
                query = "SELECT id, memory_type, content, importance, timestamp FROM twin_memories WHERE twin_id = $1"
                params = [twin_id]

                if memory_type:
                    params.append(memory_type)
                    query += f" AND memory_type = ${len(params)}"

                query += f" ORDER BY importance DESC, timestamp DESC LIMIT ${len(params) + 1}"
                params.append(limit)

                memories = await conn.fetch(query, *params)
                memories_list = [dict(m) for m in memories]

                return ToolResponse(
                    success=True,
                    message=f"Retrieved {len(memories_list)} memories",
                    data=memories_list
                )
        except Exception as e:
            return ToolResponse(success=False, message="Failed to query memories", error=str(e))


class UpdateTwinMemoryTool(BaseTool):
    """Add a memory to a digital twin"""

    def __init__(self):
        super().__init__(
            name="update_twin_memory",
            description="Add episodic, semantic, or procedural memory to a digital twin"
        )

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "twin_id": {
                "type": "string",
                "description": "UUID of the digital twin",
                "required": True
            },
            "memory_type": {
                "type": "string",
                "description": "Type of memory (episodic, semantic, procedural)",
                "required": True
            },
            "content": {
                "type": "object",
                "description": "Memory content",
                "required": True
            },
            "importance": {
                "type": "number",
                "description": "Importance weight (0.0-1.0)",
                "required": False
            }
        }

    async def execute(
        self,
        twin_id: str,
        memory_type: str,
        content: Dict[str, Any],
        importance: float = 0.5
    ) -> ToolResponse:
        try:
            pool = await DatabaseConnection.get_pool()
            async with pool.acquire() as conn:
                memory_id = await conn.fetchval(
                    """
                    INSERT INTO twin_memories (twin_id, memory_type, content, importance)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                    """,
                    twin_id, memory_type, json.dumps(content), importance
                )

                # Update twin's last interaction time
                await conn.execute(
                    "UPDATE digital_twins SET last_interaction = NOW(), interaction_count = interaction_count + 1 WHERE id = $1",
                    twin_id
                )

                return ToolResponse(
                    success=True,
                    message="Memory added successfully",
                    data={"memory_id": str(memory_id)}
                )
        except Exception as e:
            return ToolResponse(success=False, message="Failed to add memory", error=str(e))


class FindRelatedTwinsTool(BaseTool):
    """Find related digital twins via relationships"""

    def __init__(self):
        super().__init__(
            name="find_related_twins",
            description="Discover connected digital twins through relationships"
        )

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "twin_id": {
                "type": "string",
                "description": "UUID of the digital twin",
                "required": True
            },
            "relationship_type": {
                "type": "string",
                "description": "Filter by relationship type (caretaker, sibling, etc.)",
                "required": False
            }
        }

    async def execute(
        self,
        twin_id: str,
        relationship_type: Optional[str] = None
    ) -> ToolResponse:
        try:
            pool = await DatabaseConnection.get_pool()
            async with pool.acquire() as conn:
                query = """
                    SELECT
                        dt.id, dt.entity_type, dt.entity_subtype,
                        tr.relationship_type, tr.metadata
                    FROM twin_relationships tr
                    JOIN digital_twins dt ON (dt.id = tr.twin_b_id OR dt.id = tr.twin_a_id)
                    WHERE (tr.twin_a_id = $1 OR tr.twin_b_id = $1) AND dt.id != $1
                """
                params = [twin_id]

                if relationship_type:
                    params.append(relationship_type)
                    query += f" AND tr.relationship_type = ${len(params)}"

                related = await conn.fetch(query, *params)
                related_list = [dict(r) for r in related]

                return ToolResponse(
                    success=True,
                    message=f"Found {len(related_list)} related twins",
                    data=related_list
                )
        except Exception as e:
            return ToolResponse(success=False, message="Failed to find related twins", error=str(e))


# Export all tools
DATABASE_TOOLS = [
    CreateOfferTool(),
    FindNeedsTool(),
    CreateMatchTool(),
    CreateDigitalTwinTool(),
    QueryTwinMemoryTool(),
    UpdateTwinMemoryTool(),
    FindRelatedTwinsTool()
]
