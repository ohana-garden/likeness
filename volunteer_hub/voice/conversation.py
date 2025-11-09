"""
Multi-Agent Conversation Orchestrator
Manages natural conversations between user and multiple agents
Handles turn-taking, interruptions, and agent handoffs
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio

from volunteer_hub.agents.base_agent import BaseAgent


class MultiAgentConversation:
    """
    Orchestrates conversations with multiple agents
    Minimum 2 agents always present (Person Agent + Host/Specialist)
    Implements natural turn-taking and instant interruption
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.agents: List[BaseAgent] = []
        self.current_speaker: Optional[BaseAgent] = None
        self.conversation_history: List[Dict[str, Any]] = []
        self.started_at = datetime.now()
        self.status = "active"

    async def add_agent(self, agent: BaseAgent):
        """Add an agent to the conversation"""
        self.agents.append(agent)

        # Record in history
        self.conversation_history.append({
            "type": "agent_joined",
            "agent_id": agent.agent_id,
            "agent_type": agent.agent_type,
            "timestamp": datetime.now().isoformat()
        })

    async def remove_agent(self, agent_id: str):
        """Remove an agent from conversation"""
        self.agents = [a for a in self.agents if a.agent_id != agent_id]

        # Record in history
        self.conversation_history.append({
            "type": "agent_left",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        })

    async def process_user_input(
        self,
        text: str,
        emotions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user input through conversation
        Returns agent response
        """

        # Stop current speaker if speaking (interruption)
        if self.current_speaker:
            await self._handle_interruption()

        # Record user turn
        self.conversation_history.append({
            "type": "user_turn",
            "text": text,
            "emotions": emotions or {},
            "timestamp": datetime.now().isoformat()
        })

        # Determine which agent should respond
        responding_agent = await self._select_responding_agent(text)

        # Get response from agent
        start_time = datetime.now()
        response_text = await responding_agent.process(text, context={
            "conversation_history": self._get_recent_history(),
            "emotions": emotions
        })
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Update current speaker
        self.current_speaker = responding_agent

        # Record agent turn
        self.conversation_history.append({
            "type": "agent_turn",
            "agent_id": responding_agent.agent_id,
            "agent_type": responding_agent.agent_type,
            "text": response_text,
            "processing_time_ms": processing_time,
            "timestamp": datetime.now().isoformat()
        })

        return {
            "text": response_text,
            "speaker": responding_agent.agent_id,
            "speaker_type": responding_agent.agent_type,
            "processing_time_ms": processing_time,
            "active_agents": [a.agent_id for a in self.agents]
        }

    async def _select_responding_agent(self, user_text: str) -> BaseAgent:
        """
        Determine which agent should respond
        Uses simple routing logic (can be enhanced with ML)
        """

        text_lower = user_text.lower()

        # Check for explicit agent mentions or task keywords
        if any(word in text_lower for word in ["garden", "harvest", "plant", "kalo"]):
            # Look for Garden agent, or use Person agent
            garden_agents = [a for a in self.agents if "garden" in a.agent_type]
            if garden_agents:
                return garden_agents[0]

        if any(word in text_lower for word in ["kitchen", "cook", "prepare", "meal"]):
            kitchen_agents = [a for a in self.agents if "kitchen" in a.agent_type]
            if kitchen_agents:
                return kitchen_agents[0]

        if any(word in text_lower for word in ["match", "coordinate", "find", "need"]):
            coordinator_agents = [a for a in self.agents if "coordinator" in a.agent_type]
            if coordinator_agents:
                return coordinator_agents[0]

        # Default to Person agent if present
        person_agents = [a for a in self.agents if a.agent_type == "person"]
        if person_agents:
            return person_agents[0]

        # Fallback to first agent
        return self.agents[0] if self.agents else None

    async def _handle_interruption(self):
        """
        Handle user interruption of current speaker
        Stop agent immediately
        """
        # Record interruption
        self.conversation_history.append({
            "type": "interruption",
            "interrupted_agent": self.current_speaker.agent_id if self.current_speaker else None,
            "timestamp": datetime.now().isoformat()
        })

        # Clear current speaker
        self.current_speaker = None

    def _get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation turns for context"""
        return self.conversation_history[-limit:]

    async def handoff_to_agent(
        self,
        from_agent: BaseAgent,
        to_agent_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> BaseAgent:
        """
        Natural handoff between agents
        Used when one agent needs specialist help
        """

        # Find target agent
        target_agents = [a for a in self.agents if a.agent_type == to_agent_type]

        if not target_agents:
            # Spawn new agent if needed
            # TODO: Implement dynamic agent spawning
            return from_agent

        target_agent = target_agents[0]

        # Record handoff
        self.conversation_history.append({
            "type": "handoff",
            "from_agent": from_agent.agent_id,
            "to_agent": target_agent.agent_id,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        })

        # Send A2A message
        await from_agent.send_message(
            to_agent=target_agent,
            message_type="handoff",
            content=context or {}
        )

        return target_agent

    async def end_session(self):
        """
        End conversation session
        Retire ephemeral agents, persist state
        """
        self.status = "ended"

        # Retire all ephemeral agents
        for agent in self.agents:
            if agent.agent_type in ["coordinator", "garden_agent", "kitchen_agent", "vehicle_agent"]:
                await agent.retire()

        # Record session end
        self.conversation_history.append({
            "type": "session_ended",
            "duration_seconds": (datetime.now() - self.started_at).total_seconds(),
            "turn_count": len([h for h in self.conversation_history if h["type"] in ["user_turn", "agent_turn"]]),
            "timestamp": datetime.now().isoformat()
        })

    def get_statistics(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        user_turns = [h for h in self.conversation_history if h["type"] == "user_turn"]
        agent_turns = [h for h in self.conversation_history if h["type"] == "agent_turn"]
        interruptions = [h for h in self.conversation_history if h["type"] == "interruption"]

        avg_response_time = 0
        if agent_turns:
            response_times = [t.get("processing_time_ms", 0) for t in agent_turns]
            avg_response_time = sum(response_times) / len(response_times)

        return {
            "session_id": self.session_id,
            "duration_seconds": (datetime.now() - self.started_at).total_seconds(),
            "user_turns": len(user_turns),
            "agent_turns": len(agent_turns),
            "interruptions": len(interruptions),
            "avg_response_time_ms": avg_response_time,
            "active_agents": len(self.agents),
            "status": self.status
        }
