from openai import AsyncOpenAI
from core.config import settings

def get_openrouter_client() -> AsyncOpenAI:
    """Returns an asynchronous OpenAI client configured for OpenRouter."""
    if not settings.OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API key is not set in environment variables.")
        
    return AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )
