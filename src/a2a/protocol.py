"""
A2A Protocol: Agent-to-Agent Communication via Prompt Passing

Agents don't call methods on each other.
They pass prompts, which the recipient executes and returns.

This is message passing in the Actor model, but with prompts as messages.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid


class MessageType(Enum):
    """Types of A2A messages"""
    QUERY = "query"  # Ask for information
    COMMAND = "command"  # Request action
    INFORM = "inform"  # Share information
    PROMPT_INJECT = "prompt_inject"  # Inject a prompt fragment


@dataclass
class A2AMessage:
    """
    An A2A message is a prompt payload sent between agents.

    The core insight: Instead of structured data, we send prompts
    that the recipient executes in their context.
    """
    message_id: str
    sender_id: str
    recipient_id: str
    message_type: MessageType
    prompt_payload: str  # The actual prompt to execute
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    reply_to: Optional[str] = None

    @staticmethod
    def create_query(
        sender_id: str,
        recipient_id: str,
        query_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> 'A2AMessage':
        """Create a query message"""
        return A2AMessage(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=MessageType.QUERY,
            prompt_payload=query_prompt,
            context=context or {}
        )

    @staticmethod
    def create_response(
        original_message: 'A2AMessage',
        response_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> 'A2AMessage':
        """Create a response to a message"""
        return A2AMessage(
            message_id=str(uuid.uuid4()),
            sender_id=original_message.recipient_id,
            recipient_id=original_message.sender_id,
            message_type=MessageType.INFORM,
            prompt_payload=response_prompt,
            context=context or {},
            reply_to=original_message.message_id
        )


class A2ARouter:
    """
    Routes messages between agents.

    This is like a message bus, but for prompts.
    """

    def __init__(self):
        # Agent registry: agent_id → Agent instance
        self._agents: Dict[str, Any] = {}

        # Message history for debugging/replay
        self._message_history: List[A2AMessage] = []

    def register_agent(self, agent):
        """Register an agent for A2A communication"""
        self._agents[agent.agent_id] = agent

    def unregister_agent(self, agent_id: str):
        """Remove an agent from the router"""
        if agent_id in self._agents:
            del self._agents[agent_id]

    async def send(self, message: A2AMessage) -> Optional[str]:
        """
        Send a message to a recipient agent.

        The recipient executes the prompt_payload in their context
        and returns the result.
        """
        # Log message
        self._message_history.append(message)

        # Find recipient
        recipient = self._agents.get(message.recipient_id)
        if not recipient:
            raise ValueError(f"Recipient agent not found: {message.recipient_id}")

        # Execute the prompt payload in recipient's context
        from ..core.prompt_engine import PromptContext

        context = PromptContext(
            variables={
                'sender_id': message.sender_id,
                'message_type': message.message_type.value,
                **message.context
            },
            memory=[],
            metadata={
                'message_id': message.message_id,
                'timestamp': message.timestamp.isoformat()
            }
        )

        # The recipient agent generates a response using the injected prompt
        response = await recipient.generate(
            user_message=message.prompt_payload,
            context=context
        )

        return response

    async def broadcast(
        self,
        sender_id: str,
        prompt_payload: str,
        recipient_ids: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Broadcast a prompt to multiple agents in parallel.

        Returns a dict of recipient_id → response.
        """
        messages = [
            A2AMessage.create_query(
                sender_id=sender_id,
                recipient_id=recipient_id,
                query_prompt=prompt_payload,
                context=context
            )
            for recipient_id in recipient_ids
        ]

        # Send all messages in parallel
        responses = await asyncio.gather(*[
            self.send(msg) for msg in messages
        ])

        # Map responses to recipient IDs
        return dict(zip(recipient_ids, responses))

    def get_conversation(
        self,
        agent_id_1: str,
        agent_id_2: str
    ) -> List[A2AMessage]:
        """Get all messages between two agents"""
        return [
            msg for msg in self._message_history
            if (msg.sender_id == agent_id_1 and msg.recipient_id == agent_id_2)
            or (msg.sender_id == agent_id_2 and msg.recipient_id == agent_id_1)
        ]


class PromptComposer:
    """
    Utilities for composing prompts for A2A communication.

    These are helper functions for creating well-formed prompt payloads.
    """

    @staticmethod
    def query_agent(
        agent_name: str,
        question: str,
        context_description: str = ""
    ) -> str:
        """Create a query prompt for another agent"""
        prompt = f"""
You are {agent_name}. You have received a query from another agent.

Question: {question}
"""
        if context_description:
            prompt += f"\nContext: {context_description}\n"

        prompt += """
Respond based on your knowledge and current state.
Your response will be used by the requesting agent to make decisions.
"""
        return prompt.strip()

    @staticmethod
    def command_agent(
        agent_name: str,
        command: str,
        parameters: Dict[str, Any],
        reason: str = ""
    ) -> str:
        """Create a command prompt for another agent"""
        params_text = "\n".join([
            f"- {key}: {value}" for key, value in parameters.items()
        ])

        prompt = f"""
You are {agent_name}. You have received a command from another agent.

Command: {command}

Parameters:
{params_text}
"""
        if reason:
            prompt += f"\nReason: {reason}\n"

        prompt += """
Execute this command using your available tools.
Report the result in a clear, structured format.
"""
        return prompt.strip()

    @staticmethod
    def inject_context(
        agent_name: str,
        context_info: str,
        task: str
    ) -> str:
        """Inject context into another agent's execution"""
        prompt = f"""
You are {agent_name}.

INJECTED CONTEXT:
{context_info}

Using this context, please: {task}
"""
        return prompt.strip()


# Global router instance
router = A2ARouter()
