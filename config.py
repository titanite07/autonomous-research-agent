"""
Configuration management for research agent
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    
    # Model Configuration
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4")
    DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.5"))
    
    # Search Configuration
    DEFAULT_MAX_PAPERS = int(os.getenv("DEFAULT_MAX_PAPERS", "20"))
    DEFAULT_CITATION_STYLE = os.getenv("DEFAULT_CITATION_STYLE", "APA")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "research_agent.log")
    
    # Output
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if not cls.OPENAI_API_KEY:
            print("❌ Error: OPENAI_API_KEY not set")
            return False
        return True


# Export config instance
config = Config()
