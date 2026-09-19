import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root or config directory
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

class Settings:
    # Ollama AI Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")
    OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "")
    
    # Alternative API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Instagram Credentials (used when login wall is encountered)
    INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
    INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")
    INSTAGRAM_SESSIONID: str = os.getenv("INSTAGRAM_SESSIONID", "")
    
    # Scraping & Ingestion Settings
    HEADLESS_BROWSER: bool = os.getenv("HEADLESS_BROWSER", "True").lower() in ("true", "1", "yes")
    MAX_POSTS_TO_ANALYZE: int = int(os.getenv("MAX_POSTS_TO_ANALYZE", "12"))
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    
    # Storage
    OUTPUT_DIR: Path = BASE_DIR / "reports"

settings = Settings()
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
