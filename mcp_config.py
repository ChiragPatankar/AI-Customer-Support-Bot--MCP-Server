from pydantic import BaseSettings
from typing import Optional

class MCPSettings(BaseSettings):
    # Server Configuration
    SERVER_NAME: str = "AI Customer Support Bot"
    SERVER_VERSION: str = "1.0.0"
    SERVER_DESCRIPTION: str = "MCP Server for AI-powered customer support"
    
    # API Configuration
    API_PREFIX: str = "/mcp"
    MAX_CONTEXT_RESULTS: int = 5
    
    # Model Configuration
    MODEL_NAME: str = "cursor-ai"
    MODEL_VERSION: str = "1.0"
    
    # Context Provider Configuration
    CONTEXT_PROVIDER: str = "glama-ai"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

# Create global settings instance
mcp_settings = MCPSettings() 