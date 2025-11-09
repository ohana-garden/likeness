"""
Prompt Engine: The Core of Prompt-Based Architecture

This module treats prompts as executable functions. Every agent, digital twin,
and system component is fundamentally a prompt that can generate, modify, and
execute other prompts.
"""

from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
import re
from jinja2 import Template


@dataclass
class PromptContext:
    """Context that flows through prompt transformations"""
    variables: Dict[str, Any]
    memory: List[Dict[str, Any]]
    metadata: Dict[str, Any]

    def merge(self, other: 'PromptContext') -> 'PromptContext':
        """Compose contexts like function composition"""
        return PromptContext(
            variables={**self.variables, **other.variables},
            memory=self.memory + other.memory,
            metadata={**self.metadata, **other.metadata}
        )


class Prompt:
    """
    A Prompt is a function from context to text.

    Like lambda calculus:
    Prompt = λ(context) → text
    """

    def __init__(
        self,
        template: str,
        name: str = "unnamed_prompt",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.template = template
        self.name = name
        self.metadata = metadata or {}
        self._jinja_template = Template(template)

    def __call__(self, context: PromptContext) -> str:
        """
        Execute the prompt as a function.

        This is the core operation: context → rendered prompt
        """
        return self._jinja_template.render(
            **context.variables,
            memory=context.memory,
            metadata=context.metadata
        )

    def compose(self, other: 'Prompt') -> 'Prompt':
        """
        Compose two prompts: f ∘ g

        The result is a new prompt that applies both transformations
        """
        combined_template = f"{self.template}\n\n{other.template}"
        return Prompt(
            template=combined_template,
            name=f"{self.name}_composed_{other.name}",
            metadata={**self.metadata, **other.metadata}
        )

    def with_context(self, **kwargs) -> 'BoundPrompt':
        """
        Partially apply context (currying).

        Returns a new prompt with some variables pre-filled.
        """
        return BoundPrompt(self, kwargs)


class BoundPrompt:
    """A prompt with partially applied context (closure)"""

    def __init__(self, prompt: Prompt, bound_vars: Dict[str, Any]):
        self.prompt = prompt
        self.bound_vars = bound_vars

    def __call__(self, context: PromptContext) -> str:
        # Merge bound variables with runtime context
        merged_context = PromptContext(
            variables={**self.bound_vars, **context.variables},
            memory=context.memory,
            metadata=context.metadata
        )
        return self.prompt(merged_context)


class PromptCompiler(ABC):
    """
    Abstract base for prompt compilers.

    A compiler transforms source material (photos, audio, text)
    into executable prompts (agents, digital twins).
    """

    @abstractmethod
    async def compile(self, source: Any, context: PromptContext) -> Prompt:
        """
        Compile source material into an executable prompt.

        This is like a traditional compiler:
        Source Code → AST → Bytecode → Executable

        But here:
        Source (photo/audio) → Tokens → Knowledge → Prompt
        """
        pass


class PromptLoader:
    """
    Loads static prompt templates from files (Layer 1).

    These are the "source code" of the system.
    """

    @staticmethod
    def load(filepath: str) -> Prompt:
        """Load a prompt template from a markdown file"""
        with open(filepath, 'r') as f:
            content = f.read()

        # Extract metadata from frontmatter if present
        metadata = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                # Simple key: value parser
                frontmatter = parts[1]
                for line in frontmatter.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
                content = parts[2]

        # Extract name from first header or filename
        name_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        name = name_match.group(1) if name_match else filepath.split('/')[-1]

        return Prompt(
            template=content,
            name=name,
            metadata=metadata
        )


class PromptRegistry:
    """
    Central registry for all prompts in the system.

    Enables prompt discovery, versioning, and hot-reloading.
    """

    def __init__(self):
        self._prompts: Dict[str, Prompt] = {}
        self._versions: Dict[str, List[Prompt]] = {}

    def register(self, prompt: Prompt, version: str = "1.0.0"):
        """Register a prompt with versioning"""
        key = f"{prompt.name}@{version}"
        self._prompts[key] = prompt

        if prompt.name not in self._versions:
            self._versions[prompt.name] = []
        self._versions[prompt.name].append(prompt)

    def get(self, name: str, version: Optional[str] = None) -> Prompt:
        """Retrieve a prompt by name and optional version"""
        if version:
            key = f"{name}@{version}"
            return self._prompts.get(key)
        else:
            # Get latest version
            versions = self._versions.get(name, [])
            return versions[-1] if versions else None

    def load_directory(self, directory: str):
        """Load all prompts from a directory"""
        import os
        from pathlib import Path

        for filepath in Path(directory).rglob("*.md"):
            prompt = PromptLoader.load(str(filepath))
            self.register(prompt)


# Global registry instance
registry = PromptRegistry()
