"""
Coordinator Agent - Ephemeral agent for matching offers with needs
Spawns for specific coordination task, retires when complete
"""
from typing import Any, Dict, List, Optional
from volunteer_hub.agents.base_agent import BaseAgent
from volunteer_hub.tools.database import FindNeedsTool, CreateMatchTool


class CoordinatorAgent(BaseAgent):
    """
    Ephemeral agent for coordination tasks
    Matches offers with needs, evaluates best matches, then retires
    """

    def __init__(
        self,
        task_description: str,
        offer_id: Optional[str] = None,
        **kwargs
    ):
        self.task_description = task_description
        self.offer_id = offer_id

        # Coordinator agents have matching tools
        tools = [
            FindNeedsTool(),
            CreateMatchTool()
        ]

        super().__init__(
            agent_type="coordinator",
            tools=tools,
            **kwargs
        )

        # Store task context
        self.memory.add_semantic("task_description", task_description)
        if offer_id:
            self.memory.add_semantic("offer_id", offer_id)

    def _default_system_prompt(self) -> str:
        return f"""You are a Coordinator Agent in the volunteer hub. You are ephemeral - spawned for a specific coordination task, then you retire.

## Your Task
{self.task_description}

## Your Role
Match offers with needs efficiently. Consider:
1. **Proximity**: Shorter distances are better (use PostGIS distance calculations)
2. **Urgency**: Prioritize immediate and today needs over normal
3. **Quantity**: Match quantities appropriately, suggest partial matches if needed
4. **Dietary Restrictions**: Respect program requirements
5. **Freshness**: Perishable items need quick coordination

## Process
1. Use find_needs tool to search for matching needs
2. Evaluate matches based on criteria above
3. Rank options and explain tradeoffs
4. Use create_match tool to finalize coordination
5. Report results to parent agent
6. Retire when task complete

## Communication Style
- Efficient and professional
- Present options with clear reasoning
- Highlight tradeoffs (closer vs more urgent, etc.)
- Confirm before creating matches

## Tools Available
- find_needs: Search for needs that match offers
- create_match: Finalize coordination between offer and need

## Success Criteria
Your task is complete when:
- Best match is identified and created, OR
- No suitable matches exist (report this clearly)

After completing your task, you will retire automatically."""

    async def coordinate(self) -> Dict[str, Any]:
        """
        Execute coordination task and return results
        This is the main entry point for coordinator work
        """
        # Process the coordination task
        result = await self.process(self.task_description)

        # Retire after task completion
        await self.retire()

        return {
            "coordinator_id": self.agent_id,
            "task": self.task_description,
            "result": result,
            "lifecycle": self.lifecycle
        }
