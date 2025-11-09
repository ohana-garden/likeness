"""
Memory as Prompt Injection

Memory is not stored separately and retrieved.
Instead, memories are LITERALLY INJECTED into the prompt before execution.

This makes them immediately accessible but creates growth challenges.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class MemoryType(Enum):
    """Types of memory (following cognitive psychology)"""
    EPISODIC = "episodic"  # Personal experiences: "I remember when..."
    SEMANTIC = "semantic"  # Facts and knowledge: "I know that..."
    PROCEDURAL = "procedural"  # Skills and patterns: "I have learned..."


@dataclass
class Memory:
    """A single memory unit"""
    memory_id: str
    memory_type: MemoryType
    content: str
    timestamp: datetime
    importance: float = 0.5  # 0-1, used for retention
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_prompt_text(self) -> str:
        """
        Format this memory for prompt injection.

        Different memory types have different linguistic markers.
        """
        time_ago = self._format_time_ago()

        if self.memory_type == MemoryType.EPISODIC:
            return f"- {time_ago}: I remember {self.content}"
        elif self.memory_type == MemoryType.SEMANTIC:
            return f"- I know that {self.content}"
        elif self.memory_type == MemoryType.PROCEDURAL:
            return f"- I have learned: {self.content}"

    def _format_time_ago(self) -> str:
        """Human-readable time ago"""
        delta = datetime.now() - self.timestamp
        if delta.days > 365:
            return f"{delta.days // 365} year(s) ago"
        elif delta.days > 30:
            return f"{delta.days // 30} month(s) ago"
        elif delta.days > 0:
            return f"{delta.days} day(s) ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600} hour(s) ago"
        else:
            return "recently"


class MemoryStore:
    """
    Stores memories and injects them into prompts.

    This is the "closure" that captures an agent's environment.
    """

    def __init__(self, agent_id: str, max_prompt_memories: int = 10):
        self.agent_id = agent_id
        self.max_prompt_memories = max_prompt_memories

        # All memories (unbounded)
        self._memories: List[Memory] = []

        # Summarized memories (compressed old memories)
        self._summaries: List[str] = []

    def add_memory(
        self,
        content: str,
        memory_type: MemoryType,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """Add a new memory"""
        import uuid

        memory = Memory(
            memory_id=str(uuid.uuid4()),
            memory_type=memory_type,
            content=content,
            timestamp=datetime.now(),
            importance=importance,
            metadata=metadata or {}
        )

        self._memories.append(memory)

        # Check if we need to compress
        if len(self._memories) > self.max_prompt_memories * 2:
            self._compress_memories()

        return memory

    def _compress_memories(self):
        """
        Compress old memories into summaries.

        This is the key to preventing prompt bloat:
        - Keep recent memories full
        - Summarize old memories
        - Discard unimportant ones
        """
        # Sort by importance and recency
        scored_memories = [
            (m, m.importance + (0.1 if m.memory_type == MemoryType.EPISODIC else 0))
            for m in self._memories[:-self.max_prompt_memories]
        ]
        scored_memories.sort(key=lambda x: x[1], reverse=True)

        # Keep top important memories
        to_summarize = [m for m, score in scored_memories[:10]]

        # Create summary
        if to_summarize:
            summary_text = self._create_summary(to_summarize)
            self._summaries.append(summary_text)

        # Remove old memories (keep only recent ones)
        self._memories = self._memories[-self.max_prompt_memories:]

    def _create_summary(self, memories: List[Memory]) -> str:
        """Create a summary of multiple memories"""
        # Group by type
        by_type = {mt: [] for mt in MemoryType}
        for m in memories:
            by_type[m.memory_type].append(m.content)

        summary_parts = []

        if by_type[MemoryType.EPISODIC]:
            summary_parts.append(
                f"Early experiences: {', '.join(by_type[MemoryType.EPISODIC][:3])}"
            )

        if by_type[MemoryType.SEMANTIC]:
            summary_parts.append(
                f"Core knowledge: {', '.join(by_type[MemoryType.SEMANTIC][:3])}"
            )

        if by_type[MemoryType.PROCEDURAL]:
            summary_parts.append(
                f"Learned patterns: {', '.join(by_type[MemoryType.PROCEDURAL][:3])}"
            )

        return "; ".join(summary_parts)

    def get_prompt_injection(self) -> str:
        """
        Get the memory text to inject into the agent's prompt.

        This is the core operation: memories → prompt fragment
        """
        sections = []

        # Add summaries
        if self._summaries:
            sections.append("## Long-term Memory (Summarized)")
            for summary in self._summaries:
                sections.append(f"- {summary}")

        # Add recent memories
        if self._memories:
            sections.append("\n## Recent Memories")
            for memory in sorted(
                self._memories,
                key=lambda m: m.timestamp,
                reverse=True
            ):
                memory.access_count += 1
                sections.append(memory.to_prompt_text())

        return "\n".join(sections) if sections else "## Memories\n(No memories yet)"

    def query_memories(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 5
    ) -> List[Memory]:
        """
        Retrieve specific memories based on a query.

        In a full implementation, this would use vector similarity.
        For now, it's simple keyword matching.
        """
        filtered = self._memories

        if memory_type:
            filtered = [m for m in filtered if m.memory_type == memory_type]

        # Simple keyword matching (would be vector search in production)
        query_lower = query.lower()
        scored = [
            (m, sum(1 for word in query_lower.split() if word in m.content.lower()))
            for m in filtered
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [m for m, score in scored[:limit] if score > 0]

    def get_state(self) -> Dict[str, Any]:
        """Get state for persistence"""
        return {
            'agent_id': self.agent_id,
            'memory_count': len(self._memories),
            'summary_count': len(self._summaries),
            'memories': [
                {
                    'id': m.memory_id,
                    'type': m.memory_type.value,
                    'content': m.content,
                    'timestamp': m.timestamp.isoformat(),
                    'importance': m.importance
                }
                for m in self._memories
            ],
            'summaries': self._summaries
        }

    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'MemoryStore':
        """Restore from persisted state"""
        store = cls(agent_id=state['agent_id'])

        # Restore memories
        for m_data in state.get('memories', []):
            store._memories.append(Memory(
                memory_id=m_data['id'],
                memory_type=MemoryType(m_data['type']),
                content=m_data['content'],
                timestamp=datetime.fromisoformat(m_data['timestamp']),
                importance=m_data['importance']
            ))

        # Restore summaries
        store._summaries = state.get('summaries', [])

        return store


class MemoryInjector:
    """
    Utility for injecting memories into prompts at different positions.
    """

    @staticmethod
    def inject_into_system_prompt(
        system_prompt: str,
        memory_text: str,
        position: str = "end"
    ) -> str:
        """
        Inject memory into a system prompt.

        Positions:
        - 'start': After identity, before instructions
        - 'end': At the very end
        - 'before_tools': Before tool descriptions
        """
        if position == "start":
            # Split on first major section
            if "##" in system_prompt:
                parts = system_prompt.split("##", 1)
                return f"{parts[0]}\n\n{memory_text}\n\n##{parts[1]}"
            else:
                return f"{system_prompt}\n\n{memory_text}"

        elif position == "end":
            return f"{system_prompt}\n\n{memory_text}"

        elif position == "before_tools":
            if "## Available Tools" in system_prompt or "## Tools" in system_prompt:
                return system_prompt.replace(
                    "## Available Tools",
                    f"{memory_text}\n\n## Available Tools"
                ).replace(
                    "## Tools",
                    f"{memory_text}\n\n## Tools"
                )
            else:
                return f"{system_prompt}\n\n{memory_text}"

        return f"{system_prompt}\n\n{memory_text}"
