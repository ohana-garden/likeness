#!/usr/bin/env python3
"""
Likeness CLI: Create and interact with digital twins

Usage:
  python cli.py create <entity_type> <name>
  python cli.py talk <twin_id>
  python cli.py list
  python cli.py demo
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.prompt_engine import PromptContext, PromptRegistry
from src.compiler.digital_twin_compiler import DigitalTwinCompiler
from src.core.agent import Agent, AgentIdentity


class LikenessCLI:
    """Command-line interface for the Likeness system"""

    def __init__(self):
        self.registry = PromptRegistry()
        self.compiler = DigitalTwinCompiler()
        self.twins = {}

    async def create_twin(self, entity_type: str, name: str):
        """Create a new digital twin"""
        print(f"\n🌱 Creating digital twin: {name} ({entity_type})")
        print("─" * 60)

        # Gather context based on entity type
        context_vars = {'name': name}

        if entity_type == 'plant_kalo':
            context_vars.update({
                'variety': input("Variety (e.g., Lehua Maoli): ").strip() or "Unknown",
                'age_estimate': input("Age estimate: ").strip() or "Unknown",
                'location': input("Location: ").strip() or "Unknown",
                'water_status': 'good',
                'light_status': 'partial sun',
                'pest_status': 'none observed',
                'soil_status': 'healthy'
            })

        elif entity_type == 'person':
            context_vars.update({
                'vocal_tone': 'warm',
                'speaking_style': 'conversational',
                'languages': ['en', 'hawaiian']
            })

        context = PromptContext(
            variables=context_vars,
            memory=[],
            metadata={
                'source_type': 'text',
                'agent_id': f"{entity_type}_{name.lower().replace(' ', '_')}"
            }
        )

        print("\n🔄 Compiling digital twin...")
        compiled_prompt, memory_store = await self.compiler.compile(
            source=f"Text description: {name}",
            context=context
        )

        # Create agent
        identity = AgentIdentity(
            agent_id=context.metadata['agent_id'],
            agent_type=f"digital_twin_{entity_type}",
            name=name,
            system_prompt=compiled_prompt
        )

        twin = Agent(identity=identity)
        self.twins[identity.agent_id] = {
            'agent': twin,
            'memory': memory_store
        }

        print(f"\n✅ Digital twin '{name}' created successfully!")
        print(f"   ID: {identity.agent_id}")
        print(f"   Type: {entity_type}")

        return identity.agent_id

    async def talk_to_twin(self, twin_id: str):
        """Interactive conversation with a digital twin"""
        if twin_id not in self.twins:
            print(f"❌ Twin '{twin_id}' not found")
            return

        twin_data = self.twins[twin_id]
        twin = twin_data['agent']
        memory = twin_data['memory']

        print(f"\n💬 Talking to {twin.identity.name}")
        print("─" * 60)
        print("Type 'exit' to end conversation\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print(f"\n👋 Goodbye from {twin.identity.name}!")
                break

            if not user_input:
                continue

            # Build context with memory
            context = PromptContext(
                variables={
                    'user_message': user_input,
                    'memory_injection': memory.get_prompt_injection()
                },
                memory=[],
                metadata={}
            )

            # Generate response
            response = await twin.generate(user_input, context)

            print(f"\n{twin.identity.name}: {response}\n")

            # Add memory of this interaction
            memory.add_memory(
                content=f"User said: {user_input}. I responded: {response}",
                memory_type='episodic',
                importance=0.5
            )

    def list_twins(self):
        """List all created digital twins"""
        print("\n📋 Digital Twins")
        print("─" * 60)

        if not self.twins:
            print("No digital twins created yet.")
            print("\nTry: python cli.py create plant_kalo \"My Kalo\"")
            return

        for twin_id, twin_data in self.twins.items():
            agent = twin_data['agent']
            memory_count = len(twin_data['memory']._memories)

            print(f"• {agent.identity.name}")
            print(f"  ID: {twin_id}")
            print(f"  Type: {agent.identity.agent_type}")
            print(f"  Memories: {memory_count}")
            print()

    async def run_demo(self):
        """Run a demonstration of the system"""
        print("\n" + "═" * 60)
        print("  LIKENESS SYSTEM DEMO")
        print("  Prompt-Based Digital Twin Architecture")
        print("═" * 60)

        print("\n📝 This demo will:")
        print("  1. Create a kalo plant digital twin")
        print("  2. Have a brief conversation with it")
        print("  3. Show memory persistence")

        input("\nPress Enter to continue...")

        # Create a kalo twin
        print("\n" + "─" * 60)
        print("STEP 1: Creating a kalo digital twin")
        print("─" * 60)

        context = PromptContext(
            variables={
                'name': 'Hāloa',
                'variety': 'Lehua Maoli',
                'age_estimate': '4 months',
                'location': 'Demo Garden',
                'water_status': 'good',
                'light_status': 'partial sun',
                'pest_status': 'minor thrips',
                'soil_status': 'rich and moist',
                'planting_day': '2024-07-01'
            },
            memory=[],
            metadata={
                'source_type': 'text',
                'agent_id': 'demo_kalo_haloa'
            }
        )

        compiled_prompt, memory_store = await self.compiler.compile(
            source="Demo kalo plant",
            context=context
        )

        identity = AgentIdentity(
            agent_id='demo_kalo_haloa',
            agent_type='digital_twin_plant_kalo',
            name='Hāloa',
            system_prompt=compiled_prompt
        )

        twin = Agent(identity=identity)

        print("✅ Digital twin 'Hāloa' created")

        # Show the compiled prompt (first 500 chars)
        print("\n" + "─" * 60)
        print("COMPILED PROMPT (excerpt):")
        print("─" * 60)
        sample_prompt = compiled_prompt(context)
        print(sample_prompt[:500])
        print("\n... (truncated)\n")

        input("Press Enter to continue...")

        # Have a conversation
        print("\n" + "─" * 60)
        print("STEP 2: Conversation with Hāloa")
        print("─" * 60)

        conversations = [
            "How are you feeling today?",
            "Do you need anything?",
            "Tell me about your lineage"
        ]

        for msg in conversations:
            print(f"\n🧑 You: {msg}")

            conv_context = PromptContext(
                variables={
                    'user_message': msg,
                    'memory_injection': memory_store.get_prompt_injection(),
                    **context.variables
                },
                memory=[],
                metadata={}
            )

            response = await twin.generate(msg, conv_context)
            print(f"🌱 Hāloa: {response}")

            # Add memory
            memory_store.add_memory(
                content=f"Person asked: {msg}",
                memory_type='episodic',
                importance=0.7
            )

        # Show memory state
        input("\n\nPress Enter to see memory state...")

        print("\n" + "─" * 60)
        print("STEP 3: Memory State")
        print("─" * 60)
        print(memory_store.get_prompt_injection())

        print("\n\n" + "═" * 60)
        print("✅ Demo complete!")
        print("═" * 60)

        print("\nKey concepts demonstrated:")
        print("• Layer 3 prompt compilation (photo/text → executable prompt)")
        print("• Memory as prompt injection (memories added to context)")
        print("• First-person embodied perspective (\"I am\", not \"the plant\")")
        print("• Cultural context (Hāloa, Hawaiian significance)")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Likeness: Create and interact with digital twins"
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new digital twin')
    create_parser.add_argument('entity_type', help='Entity type (plant_kalo, person, etc.)')
    create_parser.add_argument('name', help='Name of the digital twin')

    # Talk command
    talk_parser = subparsers.add_parser('talk', help='Talk to a digital twin')
    talk_parser.add_argument('twin_id', help='ID of the digital twin')

    # List command
    subparsers.add_parser('list', help='List all digital twins')

    # Demo command
    subparsers.add_parser('demo', help='Run interactive demo')

    args = parser.parse_args()

    cli = LikenessCLI()

    if args.command == 'create':
        await cli.create_twin(args.entity_type, args.name)

    elif args.command == 'talk':
        await cli.talk_to_twin(args.twin_id)

    elif args.command == 'list':
        cli.list_twins()

    elif args.command == 'demo':
        await cli.run_demo()

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
