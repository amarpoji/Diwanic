"""
Configuration loader for Diwanic.
Loads environment variables from .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from PROJECT ROOT (not from diwanic/ subfolder)
# This should work whether running from WSL (/mnt/c/...) or Windows
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)
print(f"[Config] Loading .env from: {env_path}")


class Config:
    """Configuration class that reads from environment variables."""
    
    # Scraper
    SCRAPER_BASE_URL = os.getenv("SCRAPER_BASE_URL", "https://www.aldiwan.net")
    SCRAPER_DELAY = float(os.getenv("SCRAPER_DELAY", "1.5"))
    
    # Embedding
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
    
    # Qdrant
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_URL = os.getenv("QDRANT_URL", "")  # For cloud: https://xxxxx.cloud.qdrant.io
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    
    # Database (optional)
    DATABASE_URL = os.getenv("DATABASE_URL", "")


config = Config()