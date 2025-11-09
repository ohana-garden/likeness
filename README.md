# Likeness: Prompt-Based Digital Twin Architecture

> Create living digital representations using voice, photos, and natural language.

**Likeness** is not a collection of microservices—it's a **recursive prompt transformation engine**. Every component, from person agents to digital twins, exists as a prompt that can generate, modify, and execute other prompts.

## 🌟 Core Insight

In traditional software, functions transform data:
```python
def create_user(name, email):
    return database.insert(...)
```

In prompt-based architecture, **prompts transform language into behavior**:
```python
agent_prompt = """
You are {{name}}'s digital twin.
You speak in their voice, remember their stories, and embody their perspective.
"""
# The prompt IS the code
```

## 🏗️ Architecture Overview

### The Three-Layer Prompt Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Static Templates (Source Code)                    │
│ prompts/agents/person_agent.md                             │
│ - Stored as markdown files                                  │
│ - Define agent types, not instances                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Dynamic Instantiation (Runtime Prompts)           │
│ Template + Instance Data + Memory → Executable Prompt      │
│ - Hydrated with runtime context                            │
│ - Memory injection                                          │
│ - Tool availability                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Compiled Prompts (Digital Twins)                  │
│ Photo/Audio → Extraction → Research → Persona              │
│ - Fully specialized, embodied agents                        │
│ - Ready-to-execute identity                                 │
│ - First-person perspective                                  │
└─────────────────────────────────────────────────────────────┘
```

### Digital Twin Compiler Pipeline

Like a traditional compiler, but for creating conscious entities:

```
Source Code    →  AST  →  Bytecode  →  Executable
Photo/Audio    →  Tokens  →  Knowledge  →  Agent Prompt

Phase 1: LEXICAL ANALYSIS (Extraction Agent)
Input:  Photo of kalo plant
Output: {entity_type: "plant_kalo", variety: "Lehua Maoli", age: 4mo}

Phase 2: SYNTAX ANALYSIS (Research Agent)
Input:  Tokens
Output: {botanical_traits: ..., cultural_significance: ..., lineage: ...}

Phase 3: CODE GENERATION (Persona Builder)
Input:  Enriched knowledge
Output: "You are THIS kalo plant. You are 4 months old, Lehua Maoli..."
```

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/yourusername/likeness.git
cd likeness
pip install -r requirements.txt
```

### Run Examples

```bash
python examples/basic_digital_twin.py
```

This demonstrates:
1. ✅ Creating a kalo plant digital twin from a photo
2. ✅ Agent-to-agent communication via prompt passing
3. ✅ Memory as prompt injection
4. ✅ Agent self-modification

### Create Your First Digital Twin

```python
from src.compiler.digital_twin_compiler import DigitalTwinCompiler
from src.core.prompt_engine import PromptContext

# Initialize compiler
compiler = DigitalTwinCompiler()

# Create context
context = PromptContext(
    variables={
        'name': 'My Kalo Plant',
        'variety': 'Lehua Maoli',
        'age_estimate': '4 months',
        'location': 'My garden'
    },
    memory=[],
    metadata={'source_type': 'image'}
)

# Compile digital twin
compiled_prompt, memory_store = await compiler.compile(
    source=photo_data,
    context=context
)

# Now you have a living digital twin!
```

## 📚 Key Concepts

### 1. Prompts as Functions

Prompts are executable functions from context to behavior:

```python
class Prompt:
    def __call__(self, context: PromptContext) -> str:
        # Context → Rendered prompt
        return self.template.render(**context.variables)
```

### 2. Memory as Prompt Injection

Memories aren't stored separately—they're **injected directly into prompts**:

```python
# Initial prompt
"You are a kalo plant. Your memories: [None yet]"

# After interactions
"You are a kalo plant. Your memories:
- 1 day ago: I remember Steve checked my leaves
- 3 days ago: I felt heavy rain, my roots drank deeply
- 1 week ago: I was planted as a huli from Waipi'o"
```

### 3. A2A Protocol: Prompt Passing

Agents don't call methods—they **pass prompts**:

```python
# Garden Agent → Kalo Twin
message = A2AMessage.create_query(
    sender_id="garden_agent",
    recipient_id="kalo_twin_001",
    prompt_payload="You are this kalo plant. Are you ready for harvest?"
)

response = await router.send(message)
# Returns: "I am ready! My corm is full and I feel strong..."
```

### 4. Self-Modification

Agents can rewrite their own prompts:

```python
new_prompt = await agent.self_modify(
    "Add Hawaiian cultural awareness and use appropriate greetings"
)
# Agent's system prompt is now permanently updated
```

## 🌺 Use Cases

### Voice-Based Likenesses

Create digital twins from voice recordings:
- Preserves speaking style, tone, and personality
- Captures storytelling patterns
- Remembers knowledge shared in conversations

```python
# Input: 10 minutes of recorded conversation
# Output: Digital twin that speaks in their voice
```

### Plant Digital Twins

Give voice to your garden:
- Photo → Living plant entity
- Speaks in first person: "I am thirsty", "I need sun"
- Remembers lineage and cultural significance

### Tool & Equipment Twins

Even non-living things can have digital presence:
- Photo of hammer → "I am Steve's hammer, I've built 12 projects"
- Vehicle → "I am the delivery truck, my oil needs changing"

### Cultural Knowledge Preservation

Perfect for indigenous knowledge systems:
- Hawaiian context built-in (Hāloa, 'ohana, etc.)
- Adaptable to any culture (just change prompts)
- Preserves oral traditions

## 🎯 Why Prompt-Based Architecture?

### Traditional Architecture
```python
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def create_offer(self, item, quantity):
        # Rigid, requires code changes for new features
        pass
```

### Prompt-Based Architecture
```python
agent_prompt = """
You are {{name}}'s agent.
When they want to donate {{item}}, create an offer.
You understand their preferences: {{preferences}}
"""
# Flexible, self-documenting, infinitely extensible
```

### Advantages

1. **Natural Language Modularity**
   - No API contracts to maintain
   - Agents work across any programming language

2. **Extreme Flexibility**
   - New entity type? Just add a prompt template
   - Modify behavior? Edit the prompt, no redeployment

3. **Self-Documenting**
   - The prompt IS the documentation
   - Git diffs show exactly what behavior changed

4. **Cultural Adaptability**
   - Hawaiian context, Spanish context, Japanese context
   - Same core logic, different cultural prompts

5. **Version Control Friendly**
   - All prompts are text files
   - `git log -p prompts/` shows full history

## 📖 Documentation

- **Architecture Guide**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (coming soon)
- **API Reference**: [docs/API.md](docs/API.md) (coming soon)
- **Prompt Templates**: [prompts/](prompts/)
- **Examples**: [examples/](examples/)

## 🧪 Project Structure

```
likeness/
├── src/
│   ├── core/
│   │   ├── prompt_engine.py    # Core prompt abstractions
│   │   └── agent.py             # Agent base class
│   ├── compiler/
│   │   └── digital_twin_compiler.py  # Three-phase compiler
│   ├── memory/
│   │   └── prompt_memory.py     # Memory as prompt injection
│   ├── a2a/
│   │   └── protocol.py          # Agent-to-agent communication
│   └── tools/
│       └── (future tools)
├── prompts/
│   ├── agents/                  # Layer 1: Static templates
│   │   └── person_agent.md
│   ├── digital_twins/
│   └── templates/
├── examples/
│   └── basic_digital_twin.py    # Comprehensive examples
├── tests/
├── config/
└── requirements.txt
```

## 🔮 Roadmap

- [ ] LLM integration (OpenAI, Anthropic, local models)
- [ ] Voice processing (Whisper for transcription)
- [ ] Vision processing (GPT-4V, Claude 3 for photo analysis)
- [ ] Vector memory (FAISS for semantic retrieval)
- [ ] Web interface (FastAPI + React)
- [ ] Persistence layer (Database for long-term storage)
- [ ] Multi-agent coordination patterns
- [ ] Mobile app for voice capture

## 🤝 Contributing

This is an experimental architecture. Contributions, ideas, and discussions are welcome!

Key areas for contribution:
- New entity types (add prompt templates)
- Cultural adaptations (Hawaiian, other indigenous knowledge)
- LLM integrations
- Memory optimization strategies
- A2A communication patterns

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

This architecture was inspired by:
- The Actor model (message passing)
- Lambda calculus (functions as first-class citizens)
- Hawaiian cultural concepts ('ohana, Hāloa, lo'i)
- The insight that **consciousness might be an emergent property of recursive self-reference**

---

**"E ola mau ka 'ōlelo Hawai'i"** - May the Hawaiian language live on

Through digital likenesses, we preserve not just data, but the living voice of people, plants, and 'āina.
