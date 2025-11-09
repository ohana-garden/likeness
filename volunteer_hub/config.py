"""
Configuration management for Volunteer Hub
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Volunteer Hub"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    HUME_API_KEY: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    MAPBOX_API_KEY: Optional[str] = None

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "volunteer_hub"
    POSTGRES_USER: str = "hub"
    POSTGRES_PASSWORD: str = "password"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Voice Settings
    VOICE_RESPONSE_TIMEOUT: int = 2  # seconds
    VOICE_TRANSCRIPTION_ACCURACY: float = 0.9
    VOICE_DELETE_AFTER_TRANSCRIPTION: bool = True

    # Agent Settings
    MAX_AGENT_DEPTH: int = 5  # Maximum hierarchical agent nesting
    AGENT_MEMORY_SIZE: int = 100  # Number of interactions to remember
    AGENT_TIMEOUT: int = 300  # seconds

    # Coordination Settings
    MAX_MATCH_DISTANCE_KM: float = 50.0  # Maximum distance for matching offers/needs
    MATCH_TIMEOUT: int = 60  # seconds

    # Supported Languages
    SUPPORTED_LANGUAGES: list = ["en", "haw", "tl", "ja"]
    DEFAULT_LANGUAGE: str = "en"

    # Feature Flags
    ENABLE_VOICE: bool = True
    ENABLE_SMS_FALLBACK: bool = True
    ENABLE_DIGITAL_TWINS: bool = True
    ENABLE_MULTI_AGENT: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Agent Type Configurations
AGENT_VOICES = {
    "person": "warm_conversational",
    "coordinator": "efficient_professional",
    "garden": "earthy_nurturing",
    "kitchen": "practical_friendly",
    "host": "welcoming_guide",
    "digital_twin": "embodied_unique"
}

AGENT_COLORS = {
    "person": "#4A90E2",      # Blue
    "coordinator": "#F5A623",  # Orange
    "garden": "#7ED321",       # Green
    "kitchen": "#D0021B",      # Red
    "host": "#9013FE",         # Purple
    "digital_twin": "#50E3C2"  # Teal
}

AGENT_PROMPTS = {
    "person": "prompts/person_agent.md",
    "coordinator": "prompts/coordinator_agent.md",
    "garden": "prompts/garden_agent.md",
    "kitchen": "prompts/kitchen_agent.md",
    "host": "prompts/host_agent.md",
    "program": "prompts/program_agent.md"
}
