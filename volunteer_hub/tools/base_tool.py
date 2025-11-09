"""
Base Tool Class - Following Agent Zero tool patterns
Tools provide specific capabilities to agents
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ToolResponse:
    """Standard response from tool execution"""

    def __init__(
        self,
        success: bool,
        message: str,
        data: Optional[Any] = None,
        error: Optional[str] = None
    ):
        self.success = success
        self.message = message
        self.data = data
        self.error = error

    def __str__(self) -> str:
        if self.success:
            return f"{self.message}\nData: {self.data}" if self.data else self.message
        else:
            return f"Error: {self.error or self.message}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error
        }


class BaseTool(ABC):
    """
    Base class for all tools
    Following Agent Zero patterns for tool definitions
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResponse:
        """Execute the tool with given parameters"""
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Return parameter schema for this tool"""
        pass

    def to_anthropic_tool(self) -> Dict[str, Any]:
        """Convert to Anthropic tool definition format"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.get_parameters(),
                "required": self._get_required_params()
            }
        }

    def _get_required_params(self) -> List[str]:
        """Extract required parameter names"""
        params = self.get_parameters()
        return [
            name for name, schema in params.items()
            if schema.get("required", False)
        ]
