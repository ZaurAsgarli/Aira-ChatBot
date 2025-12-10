import os
import sys
from functools import lru_cache
from typing import List, Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# 1. Force load .env file immediately
load_dotenv()


class Settings(BaseSettings):
    """
    Global Application Configuration.
    Validates environment variables and provides centralized access to settings.
    """

    # Allow extra fields in .env that are not defined here (prevents crashing)
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ==========================================
    # 🔐 APPLICATION SETTINGS
    # ==========================================
    APP_NAME: str = "MynEra Aira Chatbot"

    # ✅ ƏLAVƏ EDİLDİ: Versiya nəzarəti üçün
    VERSION: str = "1.0.0"

    ENVIRONMENT: str = "production"
    DEBUG_MODE: bool = False

    # ==========================================
    # 🧠 OPENAI CONFIGURATION
    # ==========================================
    # We use Optional so the app doesn't crash immediately on import if key is missing
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    LLM_MODEL_MAIN: str = "gpt-4o-mini"
    LLM_MODEL_EMBEDDING: str = "text-embedding-3-small"
    LLM_TEMPERATURE: float = 0.5

    # ==========================================
    # ☁️ VECTOR DB (QDRANT)
    # ==========================================
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "http://localhost")
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")
    QDRANT_PORT: int = 6333

    # ==========================================
    # 📚 DATA COLLECTIONS
    # ==========================================
    COLLECTION_MENTORS: str = "mentors_collection"
    COLLECTION_COURSES: str = "courses_collection"
    COLLECTION_LEARNERS: str = "learners_collection"

    # ==========================================
    # 🌐 WEB SEARCH & TOOLS
    # ==========================================
    # Maps to 'DUCKDUCKGO_ENABLED' in .env, but controls Search generally
    SEARCH_ENABLED: bool = True
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")

    # ==========================================
    # 🧠 LOGIC KEYWORDS (For Orchestrator)
    # ==========================================
    # Words that trigger "Expert Mode" (Tables, Facts) instead of "Coach Mode"
    KEYWORD_UNIVERSITY: List[str] = [
        "universitet",
        "dim",
        "bal",
        "ixtisas",
        "bakalavr",
        "magistr",
        "qəbul",
        "admission",
        "university",
        "score",
        "imtahan",
        "tuition",
        "illik",
        "haqqı",
        "fakültə",
        "kod",
        "ixtisas kodu",
    ]


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()

# --- Startup Validation Print ---
# This runs once when you start the app to show you what is working
if __name__ != "__main__":
    # Only print this if imported, not if run directly
    print("\n--- ⚙️ CONFIG LOADED ---")

    # ✅ BURADA ARTIQ VERSION İŞLƏYƏCƏK
    print(f"✅ App: {settings.APP_NAME} v{settings.VERSION} ({settings.ENVIRONMENT})")

    if settings.OPENAI_API_KEY:
        print(f"✅ OpenAI Key: Loaded ({settings.OPENAI_API_KEY[:5]}...)")
    else:
        print("❌ OpenAI Key: MISSING! (Check .env)")

    if settings.TAVILY_API_KEY and settings.TAVILY_API_KEY.startswith("tvly"):
        print(f"✅ Tavily Key: Loaded ({settings.TAVILY_API_KEY[:5]}...)")
    else:
        print("⚠️ Tavily Key: MISSING or Invalid! Web search will not work.")
    print("------------------------\n")
