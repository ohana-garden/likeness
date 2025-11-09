"""
Example: Creating a Digital Twin using Prompt-Based Architecture

This demonstrates the full three-layer prompt hierarchy:
1. Layer 1: Static template (prompts/agents/*.md)
2. Layer 2: Runtime instantiation with context
3. Layer 3: Compiled digital twin prompt

And shows:
- Memory as prompt injection
- A2A communication via prompt passing
- Agent self-modification
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.prompt_engine import (
    Prompt, PromptContext, PromptLoader, PromptRegistry
)
from src.core.agent import Agent, AgentIdentity, AgentFactory, Tool
from src.compiler.digital_twin_compiler import DigitalTwinCompiler
from src.memory.prompt_memory import MemoryStore, MemoryType, MemoryInjector
from src.a2a.protocol import A2AMessage, A2ARouter, PromptComposer


# ============================================================================
# Example 1: Creating a Kalo Digital Twin from Photo
# ============================================================================

async def example_create_kalo_twin():
    """
    Demonstrate the digital twin compiler pipeline.

    Input: Photo of kalo + context
    Output: Executable digital twin agent
    """
    print("=" * 70)
    print("EXAMPLE 1: Creating a Kalo Digital Twin")
    print("=" * 70)

    # Initialize compiler
    compiler = DigitalTwinCompiler()

    # Create context
    context = PromptContext(
        variables={
            'name': 'Kalo-001',
            'context_description': "Steve's lo'i in Lower Puna",
            'expected_type': 'plant_kalo',
            'variety': 'Lehua Maoli',
            'age_estimate': '4 months',
            'water_status': 'good',
            'light_status': 'partial sun',
            'pest_status': 'minor thrips on leaf margins',
            'soil_status': 'rich and moist',
            'planting_day': '2024-07-01',
            'location': "Steve's lo'i, Lower Puna, Hawaii"
        },
        memory=[],
        metadata={
            'source_type': 'image',
            'agent_id': 'kalo_twin_001'
        }
    )

    # Add lineage information
    context.variables['lineage'] = {
        'mother': "Aunty Momi's huli",
        'origin': "Waipi'o Valley",
        'generation': 3
    }

    # Compile the digital twin
    print("\n📸 Source: Photo of kalo plant")
    print("🔄 Running compilation pipeline...")
    print("   Phase 1: Extracting visual features...")
    print("   Phase 2: Researching kalo knowledge...")
    print("   Phase 3: Generating persona...")

    compiled_prompt, memory_store = await compiler.compile(
        source="[photo_data_placeholder]",
        context=context
    )

    print("\n✅ Digital twin compiled successfully!")
    print(f"\nPrompt name: {compiled_prompt.name}")
    print(f"Metadata: {compiled_prompt.metadata}")

    # Show a sample of the compiled prompt
    sample_context = PromptContext(
        variables={
            **context.variables,
            'current_task': "Introduce yourself to Steve who just checked on you"
        },
        memory=[],
        metadata={}
    )

    compiled_text = compiled_prompt(sample_context)
    print("\n" + "─" * 70)
    print("COMPILED PROMPT (Layer 3):")
    print("─" * 70)
    print(compiled_text[:800])
    print("\n... (truncated)")
    print("─" * 70)

    # Add a memory
    memory_store.add_memory(
        content="Steve visited and checked my leaves for thrips",
        memory_type=MemoryType.EPISODIC,
        importance=0.7
    )

    print("\n💭 Memory added: Steve's visit")
    print("\nMemory injection:")
    print(memory_store.get_prompt_injection())

    return compiled_prompt, memory_store


# ============================================================================
# Example 2: Agent-to-Agent Communication (A2A Protocol)
# ============================================================================

async def example_a2a_communication():
    """
    Demonstrate A2A protocol with prompt passing.

    Person Agent → Garden Agent: "What kalo is ready?"
    Garden Agent → Kalo Twins: "Are you ready for harvest?"
    """
    print("\n\n" + "=" * 70)
    print("EXAMPLE 2: Agent-to-Agent Communication via Prompt Passing")
    print("=" * 70)

    # Create router
    router = A2ARouter()

    # Create Person Agent (Layer 1 → Layer 2)
    person_prompt = Prompt(
        template="""
You are Steve's personal agent. You help coordinate garden activities.

Current request: {{user_message}}

You can query other agents using A2A protocol.
""",
        name="person_agent_steve"
    )

    person_identity = AgentIdentity(
        agent_id="person_steve",
        agent_type="person_agent",
        name="Steve's Agent",
        system_prompt=person_prompt
    )

    person_agent = Agent(identity=person_identity)
    router.register_agent(person_agent)

    # Create Garden Agent
    garden_prompt = Prompt(
        template="""
You are the Garden Agent for Steve's lo'i.

You coordinate between kalo plants and farmers.

Available actions:
- Query individual kalo twins about readiness
- Aggregate responses
- Create harvest recommendations
""",
        name="garden_agent"
    )

    garden_identity = AgentIdentity(
        agent_id="garden_agent_001",
        agent_type="garden_agent",
        name="Lower Puna Lo'i Agent",
        system_prompt=garden_prompt
    )

    garden_agent = Agent(identity=garden_identity)
    router.register_agent(garden_agent)

    # Simulate A2A interaction
    print("\n👤 Person Agent → Garden Agent")

    query_message = A2AMessage.create_query(
        sender_id="person_steve",
        recipient_id="garden_agent_001",
        query_prompt=PromptComposer.query_agent(
            agent_name="Garden Agent",
            question="What kalo plants are ready for harvest?",
            context_description="Steve wants to harvest this weekend"
        ),
        context={'urgency': 'moderate', 'quantity_needed': 10}
    )

    print(f"📤 Sending message: {query_message.message_id}")
    print(f"   Type: {query_message.message_type.value}")
    print(f"   Prompt payload preview:")
    print(f"   {query_message.prompt_payload[:200]}...")

    response = await router.send(query_message)

    print(f"\n📥 Response received:")
    print(f"   {response}")

    # Broadcast to multiple twins
    print("\n\n🌱 Garden Agent → Multiple Kalo Twins (Broadcast)")

    kalo_twins = ["kalo_twin_001", "kalo_twin_002", "kalo_twin_003"]

    # Register mock kalo twins
    for twin_id in kalo_twins:
        twin_prompt = Prompt(
            template="""
You are a kalo plant digital twin. You are {{age}} months old.

Current state:
- Health: {{health}}
- Water: {{water}}

Question: {{user_message}}

Respond in first person about your readiness.
""",
            name=f"kalo_twin_{twin_id}"
        )

        twin_identity = AgentIdentity(
            agent_id=twin_id,
            agent_type="digital_twin_kalo",
            name=f"Kalo Twin {twin_id}",
            system_prompt=twin_prompt
        )

        twin_agent = Agent(identity=twin_identity)
        router.register_agent(twin_agent)

    # Broadcast query
    responses = await router.broadcast(
        sender_id="garden_agent_001",
        prompt_payload="You are this kalo plant. Are you ready for harvest? Consider your age, health, and corm development. Respond in first person.",
        recipient_ids=kalo_twins,
        context={'harvest_window': '6-9 months'}
    )

    print(f"📤 Broadcast sent to {len(kalo_twins)} twins")
    print("\n📥 Responses:")
    for twin_id, response in responses.items():
        print(f"   {twin_id}: {response[:100]}...")


# ============================================================================
# Example 3: Memory as Prompt Injection
# ============================================================================

async def example_memory_injection():
    """
    Demonstrate how memory modifies prompts over time.
    """
    print("\n\n" + "=" * 70)
    print("EXAMPLE 3: Memory as Prompt Injection")
    print("=" * 70)

    # Create a base prompt
    base_prompt = Prompt(
        template="""
You are a kalo plant digital twin.

{{memory_injection}}

Current question: {{user_message}}

Respond based on your identity and memories.
""",
        name="kalo_with_memory"
    )

    # Initialize memory store
    memory = MemoryStore(agent_id="kalo_example", max_prompt_memories=5)

    # Day 1: Birth
    print("\n📅 Day 1: Digital twin created")
    memory.add_memory(
        content="I was planted as a huli from Aunty Momi's garden",
        memory_type=MemoryType.EPISODIC,
        importance=1.0
    )

    context = PromptContext(
        variables={
            'memory_injection': memory.get_prompt_injection(),
            'user_message': 'How are you feeling?'
        },
        memory=[],
        metadata={}
    )

    print("\nPrompt with memory:")
    print("─" * 70)
    print(base_prompt(context))
    print("─" * 70)

    # Day 30: First observation
    print("\n📅 Day 30: First significant interaction")
    memory.add_memory(
        content="Steve visited and said I'm growing strong",
        memory_type=MemoryType.EPISODIC,
        importance=0.8
    )
    memory.add_memory(
        content="Lehua Maoli variety is drought-resistant",
        memory_type=MemoryType.SEMANTIC,
        importance=0.6
    )

    context.variables['memory_injection'] = memory.get_prompt_injection()
    context.variables['user_message'] = 'What have you learned?'

    print("\nPrompt with more memories:")
    print("─" * 70)
    print(base_prompt(context))
    print("─" * 70)

    # Day 120: Many memories
    print("\n📅 Day 120: After many interactions")
    for i in range(15):
        memory.add_memory(
            content=f"Event {i}: Various interactions and observations",
            memory_type=MemoryType.EPISODIC,
            importance=0.3
        )

    print(f"\n📊 Memory stats:")
    print(f"   Total memories: {len(memory._memories)}")
    print(f"   Summaries: {len(memory._summaries)}")

    context.variables['memory_injection'] = memory.get_prompt_injection()

    print("\nPrompt with compressed memories:")
    print("─" * 70)
    print(base_prompt(context))
    print("─" * 70)


# ============================================================================
# Example 4: Agent Self-Modification
# ============================================================================

async def example_self_modification():
    """
    Demonstrate how agents can modify their own prompts.
    """
    print("\n\n" + "=" * 70)
    print("EXAMPLE 4: Agent Self-Modification")
    print("=" * 70)

    # Create initial agent
    initial_prompt = Prompt(
        template="""
You are a basic digital assistant.

You help with: {{capabilities}}

User message: {{user_message}}
""",
        name="basic_assistant"
    )

    identity = AgentIdentity(
        agent_id="assistant_001",
        agent_type="assistant",
        name="Basic Assistant",
        system_prompt=initial_prompt
    )

    agent = Agent(identity=identity)

    print("\n📋 Initial prompt:")
    context = PromptContext(
        variables={'capabilities': 'answering questions', 'user_message': 'Hello'},
        memory=[],
        metadata={}
    )
    print(agent.identity.system_prompt(context))

    # Self-modify to add Hawaiian cultural awareness
    print("\n🔄 Self-modifying to add Hawaiian cultural awareness...")

    modification_request = """
Add Hawaiian cultural awareness to this agent. It should:
1. Recognize Hawaiian terms
2. Understand 'ohana and community values
3. Respect cultural protocols
4. Use appropriate Hawaiian greetings
"""

    new_prompt = await agent.self_modify(modification_request)

    print("\n📋 Modified prompt:")
    print(new_prompt.template[:400])
    print("\n... (showing first 400 chars)")

    print(f"\n✅ Agent successfully modified itself")
    print(f"   Old version: {initial_prompt.name}")
    print(f"   New version: {new_prompt.name}")


# ============================================================================
# Main Runner
# ============================================================================

async def main():
    """Run all examples"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "PROMPT-BASED ARCHITECTURE EXAMPLES" + " " * 19 + "║")
    print("║" + " " * 20 + "Likeness System Demo" + " " * 28 + "║")
    print("╚" + "═" * 68 + "╝")

    try:
        # Example 1: Digital Twin Compilation
        await example_create_kalo_twin()

        # Example 2: A2A Communication
        await example_a2a_communication()

        # Example 3: Memory Injection
        await example_memory_injection()

        # Example 4: Self-Modification
        await example_self_modification()

        print("\n\n" + "═" * 70)
        print("✅ All examples completed successfully!")
        print("═" * 70)

        print("\n📚 Key Concepts Demonstrated:")
        print("  1. Three-layer prompt hierarchy (Static → Runtime → Compiled)")
        print("  2. Digital twin compilation (Photo → Tokens → Knowledge → Prompt)")
        print("  3. Memory as prompt injection (Dynamic context growth)")
        print("  4. A2A protocol (Prompt passing between agents)")
        print("  5. Agent self-modification (Prompts rewriting prompts)")

        print("\n🎯 Prompt-Based Architecture Benefits:")
        print("  • Natural language is the universal interface")
        print("  • Agents are composable and recursive")
        print("  • System is self-documenting (prompts ARE the docs)")
        print("  • Culturally adaptable (same logic, different prompts)")
        print("  • Infinitely extensible (new entity types = new templates)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
