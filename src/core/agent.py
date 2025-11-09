"""
Agent: An Executable Prompt with Memory and Tools

Agents are not objects in the traditional OOP sense.
They are prompts that can:
1. Generate responses (execute)
2. Modify themselves (self-modification)
3. Spawn other agents (recursion)
4. Pass prompts to other agents (A2A protocol)
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime
import uuid

from .prompt_engine import Prompt, PromptContext


@dataclass
class Message:
    """A message in agent conversation"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentIdentity:
    """The identity of an agent (who it is)"""
    agent_id: str
    agent_type: str
    name: str
    system_prompt: Prompt
    created_at: datetime = field(default_factory=datetime.now)


class Tool(ABC):
    """
    Tools are capabilities that agents can invoke.

    Each tool is itself a prompt transformation:
    Input → Tool Prompt → LLM → Structured Output
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters"""
        pass

    def to_prompt_description(self) -> str:
        """
        Describe this tool in prompt format.

        This gets injected into the agent's system prompt.
        """
        return f"- {self.name}: {self.description}"


class Agent:
    """
    An agent is fundamentally an executable prompt with:
    - Identity (system prompt)
    - Memory (conversation history)
    - Tools (capabilities)
    - LLM interface (execution engine)
    """

    def __init__(
        self,
        identity: AgentIdentity,
        tools: Optional[List[Tool]] = None,
        llm_client: Optional[Any] = None,
        parent_id: Optional[str] = None
    ):
        self.identity = identity
        self.tools = tools or []
        self.llm_client = llm_client
        self.parent_id = parent_id

        # Memory as conversation history
        self.conversation: List[Message] = []

        # Subordinate agents spawned by this agent
        self.subordinates: Dict[str, 'Agent'] = {}

    @property
    def agent_id(self) -> str:
        return self.identity.agent_id

    def _build_runtime_prompt(self, context: PromptContext) -> str:
        """
        Layer 2: Build the runtime prompt by hydrating the template.

        This combines:
        - Static template (Layer 1)
        - Runtime context (instance data)
        - Memory (conversation history)
        - Available tools
        """
        # Add tools to context
        if self.tools:
            tools_description = "\n".join([
                tool.to_prompt_description() for tool in self.tools
            ])
            context.variables['available_tools'] = tools_description

        # Add conversation memory
        if self.conversation:
            memory_text = self._format_memory()
            context.memory.append({
                'type': 'conversation',
                'content': memory_text
            })

        # Execute the prompt function
        return self.identity.system_prompt(context)

    def _format_memory(self) -> str:
        """Format conversation history for prompt injection"""
        formatted = []
        for msg in self.conversation[-10:]:  # Last 10 messages
            timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M")
            formatted.append(f"[{timestamp}] {msg.role}: {msg.content}")
        return "\n".join(formatted)

    async def generate(
        self,
        user_message: str,
        context: Optional[PromptContext] = None
    ) -> str:
        """
        Generate a response by executing the agent's prompt.

        This is the core operation:
        User Input + Agent Identity + Memory → LLM → Response
        """
        # Record user message
        self.conversation.append(Message(
            role='user',
            content=user_message
        ))

        # Build runtime context
        if context is None:
            context = PromptContext(
                variables={'user_message': user_message},
                memory=[],
                metadata={'agent_id': self.agent_id}
            )
        else:
            context.variables['user_message'] = user_message

        # Build the full prompt (Layer 2)
        system_prompt = self._build_runtime_prompt(context)

        # Execute via LLM
        if self.llm_client:
            response = await self._call_llm(system_prompt, user_message)
        else:
            # Fallback: return the prompt itself (for testing)
            response = f"[No LLM] Prompt: {system_prompt[:200]}..."

        # Record response
        self.conversation.append(Message(
            role='assistant',
            content=response
        ))

        return response

    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """
        Call the LLM with the compiled prompt.

        This is where the prompt becomes behavior.
        """
        # This would integrate with OpenAI, Anthropic, etc.
        # For now, it's a placeholder
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ]

        # Simulated LLM call
        # In production: response = await self.llm_client.chat(messages)
        response = f"[Simulated response to: {user_message}]"

        return response

    async def spawn_subordinate(
        self,
        agent_type: str,
        system_prompt: Prompt,
        context: PromptContext,
        name: Optional[str] = None
    ) -> 'Agent':
        """
        Spawn a subordinate agent.

        This is prompt-based recursion:
        Parent Agent → Generates Child Prompt → Child Agent
        """
        subordinate_id = f"{self.agent_id}/sub_{len(self.subordinates)}"

        identity = AgentIdentity(
            agent_id=subordinate_id,
            agent_type=agent_type,
            name=name or f"{agent_type}_{subordinate_id}",
            system_prompt=system_prompt
        )

        subordinate = Agent(
            identity=identity,
            tools=self.tools,  # Inherit tools (can be overridden)
            llm_client=self.llm_client,
            parent_id=self.agent_id
        )

        self.subordinates[subordinate_id] = subordinate

        return subordinate

    def get_state_snapshot(self) -> Dict[str, Any]:
        """
        Get a snapshot of this agent's state.

        Used for persistence and debugging.
        """
        return {
            'agent_id': self.agent_id,
            'agent_type': self.identity.agent_type,
            'name': self.identity.name,
            'conversation_length': len(self.conversation),
            'subordinate_count': len(self.subordinates),
            'created_at': self.identity.created_at.isoformat()
        }

    async def self_modify(self, modification_prompt: str) -> Prompt:
        """
        Self-modification: Use LLM to rewrite own prompt.

        This is where agents become self-evolving.

        Input: Current prompt + modification instruction
        Output: New prompt
        """
        meta_prompt = f"""
You are a prompt compiler. Your task is to modify an agent's system prompt.

Current system prompt:
{self.identity.system_prompt.template}

Modification requested:
{modification_prompt}

Generate the new system prompt that incorporates this modification.
Output only the new prompt, no explanation.
"""

        if self.llm_client:
            new_prompt_text = await self._call_llm(meta_prompt, "Generate new prompt")
        else:
            new_prompt_text = self.identity.system_prompt.template

        # Create new prompt
        new_prompt = Prompt(
            template=new_prompt_text,
            name=f"{self.identity.system_prompt.name}_modified",
            metadata={'modified_at': datetime.now().isoformat()}
        )

        # Replace system prompt
        self.identity.system_prompt = new_prompt

        return new_prompt


class AgentFactory:
    """Factory for creating agents from prompt templates"""

    def __init__(self, prompt_registry, llm_client=None):
        self.registry = prompt_registry
        self.llm_client = llm_client

    def create_agent(
        self,
        agent_type: str,
        name: str,
        context: PromptContext,
        tools: Optional[List[Tool]] = None
    ) -> Agent:
        """
        Create an agent from a registered prompt template.

        This is the instantiation process (Layer 1 → Layer 2).
        """
        # Get the prompt template
        template = self.registry.get(agent_type)
        if not template:
            raise ValueError(f"No prompt template found for agent type: {agent_type}")

        # Create identity
        identity = AgentIdentity(
            agent_id=str(uuid.uuid4()),
            agent_type=agent_type,
            name=name,
            system_prompt=template
        )

        # Create agent
        agent = Agent(
            identity=identity,
            tools=tools,
            llm_client=self.llm_client
        )

        return agent
