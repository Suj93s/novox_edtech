from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    
    # Intelligent Model Routing settings
    MODEL_FLASH_LITE: str = "google/gemini-2.5-flash-lite"
    MODEL_PRO: str = "google/gemini-2.5-pro"
    MODEL_OVERRIDE: Optional[str] = None
    
    ROUTE_SIMPLE_QUESTION: str = "google/gemini-2.5-flash-lite"
    ROUTE_CODING_QUESTION: str = "google/gemini-2.5-pro"
    ROUTE_DEBUGGING_QUESTION: str = "google/gemini-2.5-pro"
    ROUTE_DOCUMENT_HEAVY_QUESTION: str = "google/gemini-2.5-pro"
    
    class Config:
        env_file = ".env"

settings = Settings()

