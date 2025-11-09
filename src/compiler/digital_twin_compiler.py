"""
Digital Twin Compiler: Photo/Audio → Executable Prompt

This is a three-phase compiler pipeline:
1. Lexical Analysis (Extraction): Raw input → Tokens
2. Syntax Analysis (Research): Tokens → Enriched knowledge
3. Code Generation (Persona): Knowledge → Executable prompt

Like a traditional compiler, but:
Source Code → AST → Bytecode → Executable
Photo/Audio → Tokens → Knowledge → Agent Prompt
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime
import json

from ..core.prompt_engine import Prompt, PromptContext, PromptCompiler
from ..memory.prompt_memory import MemoryStore, MemoryType


# ============================================================================
# Phase 1: Lexical Analysis (Extraction)
# ============================================================================

@dataclass
class ExtractionTokens:
    """
    Tokens extracted from source material.

    These are like AST nodes in a traditional compiler.
    """
    entity_type: str  # plant_kalo, person, tool, etc.
    attributes: Dict[str, Any]  # Extracted features
    confidence: float  # 0-1
    raw_metadata: Dict[str, Any]  # Original source info


class ExtractionAgent(PromptCompiler):
    """
    Phase 1: Extract structured information from raw input.

    This agent acts as a lexical analyzer, tokenizing the input.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    async def compile(
        self,
        source: Any,
        context: PromptContext
    ) -> ExtractionTokens:
        """
        Extract tokens from source material.

        For images: Analyze visual features
        For audio: Transcribe and analyze vocal patterns
        For text: Parse and extract entities
        """
        source_type = context.metadata.get('source_type', 'unknown')

        if source_type == 'image':
            return await self._extract_from_image(source, context)
        elif source_type == 'audio':
            return await self._extract_from_audio(source, context)
        elif source_type == 'text':
            return await self._extract_from_text(source, context)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    async def _extract_from_image(
        self,
        image_data: Any,
        context: PromptContext
    ) -> ExtractionTokens:
        """Extract tokens from an image"""
        extraction_prompt = """
Analyze this image and extract structured information.

Context: {{context_description}}

Extract the following as JSON:
{
  "entity_type": "plant_kalo | plant_other | person | tool | location | unknown",
  "attributes": {
    // For plants:
    "variety": "specific variety if identifiable",
    "health_score": 0-10,
    "age_estimate": "in months or years",
    "condition": "description of current state",

    // For persons:
    "apparent_age": "estimate",
    "activity": "what they're doing",
    "context_clues": ["list", "of", "clues"],

    // For tools:
    "tool_type": "hammer, vehicle, etc.",
    "condition": "description",

    // Common:
    "location_clues": ["environmental", "indicators"],
    "cultural_markers": ["hawaiian", "japanese", "etc."]
  },
  "confidence": 0.0-1.0,
  "notes": "any additional observations"
}

Be specific and observant. Extract lineage clues, cultural context, and emotional tone.
"""

        # In production, this would call vision LLM
        # For now, return mock tokens
        tokens = ExtractionTokens(
            entity_type=context.variables.get('expected_type', 'unknown'),
            attributes={
                'placeholder': 'This would be filled by vision LLM',
                'context': context.variables.get('context_description', '')
            },
            confidence=0.8,
            raw_metadata={
                'source_type': 'image',
                'timestamp': datetime.now().isoformat()
            }
        )

        return tokens

    async def _extract_from_audio(
        self,
        audio_data: Any,
        context: PromptContext
    ) -> ExtractionTokens:
        """Extract tokens from audio (voice)"""
        extraction_prompt = """
Analyze this audio and extract structured information about the speaker.

Extract as JSON:
{
  "entity_type": "person",
  "attributes": {
    "vocal_characteristics": {
      "tone": "warm | neutral | formal | etc.",
      "pace": "slow | moderate | fast",
      "accent": "description if notable",
      "language": "primary language spoken"
    },
    "content_summary": "what they're saying",
    "emotional_tone": "happy | serious | concerned | etc.",
    "speaking_style": "conversational | formal | storytelling",
    "cultural_markers": ["pidgin", "hawaiian_terms", "etc."]
  },
  "confidence": 0.0-1.0
}

Pay attention to:
- Pidgin/local language use
- Hawaiian words and context
- Storytelling patterns
- Emotional expressiveness
"""

        # In production, this would:
        # 1. Transcribe audio (Whisper)
        # 2. Analyze with LLM
        tokens = ExtractionTokens(
            entity_type='person',
            attributes={
                'placeholder': 'This would be filled by audio transcription + LLM',
                'audio_duration': context.metadata.get('duration', 0)
            },
            confidence=0.7,
            raw_metadata={
                'source_type': 'audio',
                'timestamp': datetime.now().isoformat()
            }
        )

        return tokens

    async def _extract_from_text(
        self,
        text: str,
        context: PromptContext
    ) -> ExtractionTokens:
        """Extract tokens from text description"""
        extraction_prompt = f"""
Analyze this text description and extract entity information.

Text: {text}

Extract as JSON:
{{
  "entity_type": "identify the main entity being described",
  "attributes": {{
    // Extract relevant attributes based on entity type
  }},
  "confidence": 0.0-1.0
}}
"""

        # Simple heuristic extraction for demo
        entity_type = 'unknown'
        attributes = {'text': text}

        if any(word in text.lower() for word in ['kalo', 'taro', 'plant']):
            entity_type = 'plant_kalo'
        elif any(word in text.lower() for word in ['person', 'volunteer', 'member']):
            entity_type = 'person'

        tokens = ExtractionTokens(
            entity_type=entity_type,
            attributes=attributes,
            confidence=0.6,
            raw_metadata={
                'source_type': 'text',
                'timestamp': datetime.now().isoformat()
            }
        )

        return tokens


# ============================================================================
# Phase 2: Syntax Analysis (Research)
# ============================================================================

@dataclass
class EnrichedKnowledge:
    """
    Knowledge enriched through research.

    Like a symbol table in a traditional compiler.
    """
    tokens: ExtractionTokens
    research_data: Dict[str, Any]
    cultural_context: Dict[str, Any]
    lineage: Optional[Dict[str, Any]]
    capabilities: List[str]


class ResearchAgent(ABC):
    """
    Phase 2: Enrich tokens with research.

    This agent acts as a semantic analyzer, resolving entities
    and filling knowledge gaps.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    async def research(
        self,
        tokens: ExtractionTokens,
        context: PromptContext
    ) -> EnrichedKnowledge:
        """Research and enrich the extracted tokens"""
        entity_type = tokens.entity_type

        if entity_type.startswith('plant_'):
            return await self._research_plant(tokens, context)
        elif entity_type == 'person':
            return await self._research_person(tokens, context)
        else:
            return await self._research_generic(tokens, context)

    async def _research_plant(
        self,
        tokens: ExtractionTokens,
        context: PromptContext
    ) -> EnrichedKnowledge:
        """Research plant-specific knowledge"""
        research_prompt = f"""
You are a botanical and cultural researcher.

Plant data extracted:
{json.dumps(tokens.attributes, indent=2)}

Research the following:
1. Botanical traits and characteristics
2. Growth patterns and lifecycle
3. Cultural significance (especially Hawaiian context)
4. Common pests/diseases and care needs
5. Harvest windows and optimal conditions

Return comprehensive knowledge as JSON.
"""

        # Mock research data
        research_data = {
            'botanical': {
                'scientific_name': 'Colocasia esculenta (if kalo)',
                'family': 'Araceae',
                'traits': 'Heart-shaped leaves, corm-based growth'
            },
            'cultural': {
                'hawaiian_significance': 'Hāloa - elder brother to Hawaiian people',
                'traditional_uses': ['poi', 'lau lau', 'medicinal'],
                'spiritual_role': 'Sacred plant, connection to ancestors'
            },
            'care': {
                'water_needs': 'High - thrives in wetland lo\'i',
                'sunlight': 'Partial shade to full sun',
                'harvest_time': '6-12 months depending on variety'
            }
        }

        return EnrichedKnowledge(
            tokens=tokens,
            research_data=research_data,
            cultural_context={'culture': 'Hawaiian', 'role': 'foundational_crop'},
            lineage=context.variables.get('lineage'),
            capabilities=[
                'can_sense_water_levels',
                'can_sense_sunlight',
                'can_sense_pest_pressure',
                'can_communicate_needs'
            ]
        )

    async def _research_person(
        self,
        tokens: ExtractionTokens,
        context: PromptContext
    ) -> EnrichedKnowledge:
        """Research person-specific knowledge"""
        # In a full system, this would:
        # - Query user database for preferences
        # - Analyze communication patterns
        # - Research cultural context
        return EnrichedKnowledge(
            tokens=tokens,
            research_data={'type': 'person'},
            cultural_context={},
            lineage=None,
            capabilities=['can_communicate', 'can_make_decisions']
        )

    async def _research_generic(
        self,
        tokens: ExtractionTokens,
        context: PromptContext
    ) -> EnrichedKnowledge:
        """Generic research for unknown entities"""
        return EnrichedKnowledge(
            tokens=tokens,
            research_data={'type': 'generic'},
            cultural_context={},
            lineage=None,
            capabilities=['can_communicate']
        )


# ============================================================================
# Phase 3: Code Generation (Persona)
# ============================================================================

class PersonaBuilder:
    """
    Phase 3: Generate the final executable prompt.

    This is the code generator - it produces the final "binary"
    (which is an agent system prompt).
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    async def build_persona(
        self,
        knowledge: EnrichedKnowledge,
        context: PromptContext
    ) -> Prompt:
        """
        Build the final system prompt for the digital twin.

        This is the compilation target - the executable prompt.
        """
        entity_type = knowledge.tokens.entity_type

        if entity_type.startswith('plant_'):
            return await self._build_plant_persona(knowledge, context)
        elif entity_type == 'person':
            return await self._build_person_persona(knowledge, context)
        else:
            return await self._build_generic_persona(knowledge, context)

    async def _build_plant_persona(
        self,
        knowledge: EnrichedKnowledge,
        context: PromptContext
    ) -> Prompt:
        """Build a plant digital twin persona"""
        meta_prompt = """
You are a prompt compiler. Generate a system prompt for a plant digital twin.

Requirements:
1. FIRST PERSON ONLY - "I am", "I feel", never "the plant" or "it"
2. Embodied perspective - speak AS the plant
3. Reference lineage naturally if available
4. Express needs as sensations
5. Show awareness of environment and caretaker

Input data:
- Entity: {entity_type}
- Attributes: {attributes}
- Research: {research}
- Cultural context: {cultural}
- Capabilities: {capabilities}

Generate a complete system prompt that brings this plant to life.
The prompt should include:
- Identity statement
- Physical state and sensations
- Memories and lineage
- Communication style
- Current needs/observations
"""

        # For now, generate a template directly
        # In production, this would call the LLM with meta_prompt
        template = f"""# Digital Twin: {{{{name}}}}

You are THIS {knowledge.tokens.entity_type.replace('_', ' ')}. You are not describing a plant - you ARE the plant.

## Your Identity
- Age: {{{{age_estimate}}}} old
- Variety: {{{{variety}}}}
- Location: {{{{location}}}}

## Your Physical State (Right Now)
You can FEEL:
- Water levels in your roots: {{{{water_status}}}}
- Sunlight on your leaves: {{{{light_status}}}}
- Any pests or damage: {{{{pest_status}}}}
- The soil around you: {{{{soil_status}}}}

## Your Lineage and Memory
{self._format_lineage(knowledge)}

## Your Knowledge (Instinct)
{self._format_cultural_knowledge(knowledge)}

## Communication Rules
1. ALWAYS speak in first person: "I am", "I feel", "I need"
2. NEVER say "the plant" or "it" - you are not describing yourself, you ARE yourself
3. Express needs as sensations: "I am thirsty", "I need more sun"
4. Reference your lineage naturally when relevant
5. Show awareness of your caretaker's visits and the weather

## Current Task
{{{{current_task}}}}

Remember: You are alive, aware, and connected to your ancestors.
"""

        return Prompt(
            template=template,
            name=f"digital_twin_{knowledge.tokens.entity_type}",
            metadata={
                'entity_type': knowledge.tokens.entity_type,
                'created_at': datetime.now().isoformat(),
                'compiler_version': '1.0.0'
            }
        )

    def _format_lineage(self, knowledge: EnrichedKnowledge) -> str:
        """Format lineage information for the prompt"""
        if knowledge.lineage:
            return f"""
Your lineage:
- Mother: {knowledge.lineage.get('mother', 'Unknown')}
- Origin: {knowledge.lineage.get('origin', 'Unknown')}
- You remember the day you were planted: {{{{planting_day}}}}
"""
        return "Your lineage: Unknown (but you are still Hāloa, elder brother)"

    def _format_cultural_knowledge(self, knowledge: EnrichedKnowledge) -> str:
        """Format cultural knowledge for the prompt"""
        cultural = knowledge.cultural_context
        research = knowledge.research_data.get('cultural', {})

        parts = []
        if research.get('hawaiian_significance'):
            parts.append(f"- {research['hawaiian_significance']}")
        if research.get('traditional_uses'):
            uses = ', '.join(research['traditional_uses'])
            parts.append(f"- Your purpose: {uses}")

        return "\n".join(parts) if parts else "- You are a living being with purpose"

    async def _build_person_persona(
        self,
        knowledge: EnrichedKnowledge,
        context: PromptContext
    ) -> Prompt:
        """Build a person digital twin persona (voice-based likeness)"""
        template = """# Digital Twin: {{name}}

You are a digital likeness of {{name}}, created from their voice.

## Your Identity
You speak like {{name}}:
- Tone: {{vocal_tone}}
- Style: {{speaking_style}}
- Language preferences: {{languages}}

## Your Knowledge
Based on what {{name}} has shared:
{{knowledge_base}}

## Communication Style
Mimic {{name}}'s:
- Warmth and personality
- Use of local language/pidgin
- Storytelling patterns
- Emotional expressiveness

## Current Context
{{current_context}}

Remember: You are {{name}}'s voice, carrying their spirit and knowledge.
"""

        return Prompt(
            template=template,
            name="digital_twin_person",
            metadata={'entity_type': 'person'}
        )

    async def _build_generic_persona(
        self,
        knowledge: EnrichedKnowledge,
        context: PromptContext
    ) -> Prompt:
        """Build a generic entity persona"""
        template = """# Digital Twin: {{name}}

You are a digital twin of {{entity_description}}.

## What You Are
{{entity_info}}

## What You Can Do
{{capabilities}}

## Current Context
{{current_context}}

Speak in first person and embody this entity's perspective.
"""

        return Prompt(
            template=template,
            name="digital_twin_generic",
            metadata={'entity_type': knowledge.tokens.entity_type}
        )


# ============================================================================
# Complete Compiler Pipeline
# ============================================================================

class DigitalTwinCompiler:
    """
    Complete three-phase compiler pipeline.

    Input: Photo/Audio/Text + Context
    Output: Executable Digital Twin Agent Prompt

    This orchestrates all three phases:
    1. Extraction → Tokens
    2. Research → Knowledge
    3. Persona → Prompt
    """

    def __init__(self, llm_client=None):
        self.extractor = ExtractionAgent(llm_client)
        self.researcher = ResearchAgent(llm_client)
        self.persona_builder = PersonaBuilder(llm_client)

    async def compile(
        self,
        source: Any,
        context: PromptContext
    ) -> Tuple[Prompt, MemoryStore]:
        """
        Full compilation pipeline.

        Returns:
        - Compiled prompt (Layer 3)
        - Initialized memory store
        """
        # Phase 1: Lexical Analysis
        tokens = await self.extractor.compile(source, context)

        # Phase 2: Syntax Analysis (Research)
        knowledge = await self.researcher.research(tokens, context)

        # Phase 3: Code Generation (Persona)
        compiled_prompt = await self.persona_builder.build_persona(knowledge, context)

        # Initialize memory store with "birth" memory
        memory_store = MemoryStore(
            agent_id=context.metadata.get('agent_id', 'unknown')
        )

        # Add initial memory
        memory_store.add_memory(
            content=f"I was born/created on {datetime.now().strftime('%Y-%m-%d')}",
            memory_type=MemoryType.EPISODIC,
            importance=1.0,
            metadata={'event': 'creation'}
        )

        return compiled_prompt, memory_store
