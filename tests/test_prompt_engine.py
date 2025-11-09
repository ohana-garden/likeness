"""
Tests for the core prompt engine.

These tests demonstrate how prompts function as composable, executable units.
"""

import pytest
from src.core.prompt_engine import (
    Prompt, PromptContext, BoundPrompt, PromptRegistry
)


def test_prompt_basic_rendering():
    """Test basic prompt rendering with context"""
    prompt = Prompt(
        template="Hello {{name}}, you are {{age}} years old.",
        name="greeting"
    )

    context = PromptContext(
        variables={'name': 'Alice', 'age': 30},
        memory=[],
        metadata={}
    )

    result = prompt(context)
    assert result == "Hello Alice, you are 30 years old."


def test_prompt_composition():
    """Test composing two prompts"""
    prompt1 = Prompt(
        template="You are {{role}}.",
        name="identity"
    )

    prompt2 = Prompt(
        template="Your task: {{task}}",
        name="task"
    )

    composed = prompt1.compose(prompt2)

    context = PromptContext(
        variables={'role': 'assistant', 'task': 'help users'},
        memory=[],
        metadata={}
    )

    result = composed(context)
    assert "You are assistant" in result
    assert "Your task: help users" in result


def test_prompt_with_memory():
    """Test memory injection into prompts"""
    prompt = Prompt(
        template="""
You are an agent.

## Memories
{% for mem in memory %}
- {{mem.content}}
{% endfor %}

Current task: {{task}}
""",
        name="agent_with_memory"
    )

    context = PromptContext(
        variables={'task': 'respond to user'},
        memory=[
            {'content': 'User prefers concise responses'},
            {'content': 'Previous topic was gardening'}
        ],
        metadata={}
    )

    result = prompt(context)
    assert "User prefers concise responses" in result
    assert "Previous topic was gardening" in result


def test_bound_prompt():
    """Test partial application (currying) of prompts"""
    prompt = Prompt(
        template="Hello {{name}}, your role is {{role}}",
        name="greeting"
    )

    # Bind 'name' but leave 'role' for later
    bound = prompt.with_context(name="Alice")

    context = PromptContext(
        variables={'role': 'developer'},
        memory=[],
        metadata={}
    )

    result = bound(context)
    assert "Hello Alice" in result
    assert "your role is developer" in result


def test_prompt_registry():
    """Test prompt registry for version management"""
    registry = PromptRegistry()

    # Register v1
    prompt_v1 = Prompt(
        template="Version 1: {{message}}",
        name="test_prompt"
    )
    registry.register(prompt_v1, version="1.0.0")

    # Register v2
    prompt_v2 = Prompt(
        template="Version 2: {{message}} (enhanced)",
        name="test_prompt"
    )
    registry.register(prompt_v2, version="2.0.0")

    # Get specific version
    v1 = registry.get("test_prompt", version="1.0.0")
    v2 = registry.get("test_prompt", version="2.0.0")

    context = PromptContext(
        variables={'message': 'Hello'},
        memory=[],
        metadata={}
    )

    assert "Version 1" in v1(context)
    assert "Version 2" in v2(context)

    # Get latest (should be v2)
    latest = registry.get("test_prompt")
    assert latest is prompt_v2


def test_context_merging():
    """Test merging contexts (composing closures)"""
    context1 = PromptContext(
        variables={'name': 'Alice', 'age': 30},
        memory=[{'content': 'Memory 1'}],
        metadata={'source': 'system'}
    )

    context2 = PromptContext(
        variables={'age': 31, 'role': 'developer'},  # age should override
        memory=[{'content': 'Memory 2'}],
        metadata={'timestamp': '2024-01-01'}
    )

    merged = context1.merge(context2)

    assert merged.variables['name'] == 'Alice'
    assert merged.variables['age'] == 31  # Overridden
    assert merged.variables['role'] == 'developer'
    assert len(merged.memory) == 2
    assert merged.metadata['source'] == 'system'
    assert merged.metadata['timestamp'] == '2024-01-01'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
