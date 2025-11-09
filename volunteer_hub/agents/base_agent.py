"""
Base Agent Class - Core framework for hierarchical agent spawning
Following Agent Zero patterns: hierarchical spawning, memory, tools, A2A communication
"""
import asyncio
import uuid
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from abc import ABC, abstractmethod
import anthropic
from anthropic import AsyncAnthropic

from volunteer_hub.config import settings


class AgentMessage:
    """Message passed between agents (A2A protocol)"""

    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.message_type = message_type
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.status = "sent"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message_type": self.message_type,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status
        }


class AgentMemory:
    """Simple memory system for agents"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.episodic: List[Dict[str, Any]] = []  # Recent interactions
        self.semantic: Dict[str, Any] = {}  # Facts and knowledge
        self.procedural: List[Dict[str, Any]] = []  # Learned patterns

    def add_episodic(self, interaction: Dict[str, Any]):
        """Add recent interaction memory"""
        self.episodic.append({
            **interaction,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only recent memories
        if len(self.episodic) > self.max_size:
            self.episodic = self.episodic[-self.max_size:]

    def add_semantic(self, key: str, value: Any):
        """Store factual knowledge"""
        self.semantic[key] = value

    def get_semantic(self, key: str, default: Any = None) -> Any:
        """Retrieve factual knowledge"""
        return self.semantic.get(key, default)

    def add_procedural(self, pattern: Dict[str, Any]):
        """Store learned behavior pattern"""
        self.procedural.append({
            **pattern,
            "learned_at": datetime.now().isoformat()
        })

    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory for persistence"""
        return {
            "episodic": self.episodic,
            "semantic": self.semantic,
            "procedural": self.procedural
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMemory':
        """Deserialize memory from persistence"""
        memory = cls()
        memory.episodic = data.get("episodic", [])
        memory.semantic = data.get("semantic", {})
        memory.procedural = data.get("procedural", [])
        return memory


class BaseAgent(ABC):
    """
    Base Agent following Agent Zero patterns:
    - Hierarchical spawning (spawn subordinate agents)
    - Tool system (agents have specific capabilities)
    - Memory persistence (remember interactions)
    - A2A communication (agents coordinate directly)
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: str = "base",
        parent_agent_id: Optional[str] = None,
        depth: int = 0,
        tools: Optional[List[Any]] = None,
        system_prompt: Optional[str] = None,
        memory: Optional[AgentMemory] = None
    ):
        self.agent_id = agent_id or f"{agent_type}_{uuid.uuid4().hex[:8]}"
        self.agent_type = agent_type
        self.parent_agent_id = parent_agent_id
        self.depth = depth
        self.tools = tools or []
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.memory = memory or AgentMemory(max_size=settings.AGENT_MEMORY_SIZE)

        # State
        self.spawned_at = datetime.now()
        self.retired_at: Optional[datetime] = None
        self.lifecycle = "active"  # active, retired, failed
        self.subordinates: List['BaseAgent'] = []  # Spawned child agents

        # AI client
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-5-20250929"

        # Message queue for A2A communication
        self.message_queue: List[AgentMessage] = []

    @abstractmethod
    def _default_system_prompt(self) -> str:
        """Subclasses define their own system prompts"""
        pass

    async def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Main processing loop - takes user input, returns response
        Similar to Agent Zero's main loop
        """
        context = context or {}

        # Add interaction to memory
        self.memory.add_episodic({
            "type": "user_input",
            "content": user_input,
            "context": context
        })

        # Build messages for Claude
        messages = self._build_messages(user_input, context)

        # Call Claude
        response = await self._call_claude(messages)

        # Process any tool calls
        if response.stop_reason == "tool_use":
            tool_results = await self._execute_tools(response.content)
            # Continue conversation with tool results
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            response = await self._call_claude(messages)

        # Extract text response
        text_response = self._extract_text(response.content)

        # Add response to memory
        self.memory.add_episodic({
            "type": "agent_response",
            "content": text_response
        })

        return text_response

    def _build_messages(self, user_input: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build message history including memory context"""
        messages = []

        # Add relevant memory context
        recent_history = self.memory.episodic[-5:]  # Last 5 interactions
        if recent_history:
            history_text = "\n".join([
                f"{m['type']}: {m.get('content', '')[:200]}"
                for m in recent_history
            ])
            messages.append({
                "role": "user",
                "content": f"<memory>\n{history_text}\n</memory>"
            })

        # Add current input
        messages.append({
            "role": "user",
            "content": user_input
        })

        return messages

    async def _call_claude(self, messages: List[Dict[str, Any]]) -> Any:
        """Call Claude API with tool support"""
        tool_defs = [tool.to_anthropic_tool() for tool in self.tools if hasattr(tool, 'to_anthropic_tool')]

        params = {
            "model": self.model,
            "max_tokens": 4096,
            "system": self.system_prompt,
            "messages": messages
        }

        if tool_defs:
            params["tools"] = tool_defs

        response = await self.client.messages.create(**params)
        return response

    async def _execute_tools(self, content: List[Any]) -> List[Dict[str, Any]]:
        """Execute tool calls and return results"""
        results = []
        for block in content:
            if block.type == "tool_use":
                tool = self._find_tool(block.name)
                if tool:
                    try:
                        result = await tool.execute(**block.input)
                        results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result)
                        })
                    except Exception as e:
                        results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {str(e)}",
                            "is_error": True
                        })
        return results

    def _find_tool(self, tool_name: str) -> Optional[Any]:
        """Find tool by name"""
        for tool in self.tools:
            if hasattr(tool, 'name') and tool.name == tool_name:
                return tool
        return None

    def _extract_text(self, content: List[Any]) -> str:
        """Extract text from Claude response"""
        text_blocks = [block.text for block in content if hasattr(block, 'text')]
        return "\n".join(text_blocks)

    async def spawn_subordinate(
        self,
        agent_class: Type['BaseAgent'],
        **kwargs
    ) -> 'BaseAgent':
        """
        Spawn a subordinate agent (hierarchical spawning pattern)
        Similar to Agent Zero's call_subordinate()
        """
        if self.depth >= settings.MAX_AGENT_DEPTH:
            raise Exception(f"Maximum agent depth ({settings.MAX_AGENT_DEPTH}) reached")

        # Create subordinate with increased depth
        subordinate = agent_class(
            parent_agent_id=self.agent_id,
            depth=self.depth + 1,
            **kwargs
        )

        self.subordinates.append(subordinate)

        # Record spawning in memory
        self.memory.add_episodic({
            "type": "subordinate_spawned",
            "agent_type": subordinate.agent_type,
            "agent_id": subordinate.agent_id
        })

        return subordinate

    async def send_message(self, to_agent: 'BaseAgent', message_type: str, content: Dict[str, Any]):
        """Send message to another agent (A2A communication)"""
        message = AgentMessage(
            from_agent=self.agent_id,
            to_agent=to_agent.agent_id,
            message_type=message_type,
            content=content
        )
        to_agent.receive_message(message)
        return message

    def receive_message(self, message: AgentMessage):
        """Receive message from another agent"""
        message.status = "received"
        self.message_queue.append(message)

        # Add to memory
        self.memory.add_episodic({
            "type": "message_received",
            "from": message.from_agent,
            "message_type": message.message_type,
            "content": message.content
        })

    async def retire(self):
        """Retire this agent (ephemeral agents clean up after task)"""
        self.lifecycle = "retired"
        self.retired_at = datetime.now()

        # Retire all subordinates
        for sub in self.subordinates:
            if sub.lifecycle == "active":
                await sub.retire()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent state for persistence"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "parent_agent_id": self.parent_agent_id,
            "depth": self.depth,
            "system_prompt": self.system_prompt,
            "memory": self.memory.to_dict(),
            "spawned_at": self.spawned_at.isoformat(),
            "retired_at": self.retired_at.isoformat() if self.retired_at else None,
            "lifecycle": self.lifecycle
        }

    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'BaseAgent':
        """Deserialize agent from persistence"""
        memory = AgentMemory.from_dict(data.get("memory", {}))
        agent = cls(
            agent_id=data["agent_id"],
            parent_agent_id=data.get("parent_agent_id"),
            depth=data.get("depth", 0),
            system_prompt=data.get("system_prompt"),
            memory=memory
        )
        agent.spawned_at = datetime.fromisoformat(data["spawned_at"])
        agent.lifecycle = data.get("lifecycle", "active")
        if data.get("retired_at"):
            agent.retired_at = datetime.fromisoformat(data["retired_at"])
        return agent
