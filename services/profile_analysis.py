from typing import List, Dict, Any
import json
import logging
from services.openrouter import get_openrouter_client

logger = logging.getLogger(__name__)

PROFILE_ANALYSIS_SYSTEM_PROMPT = """
You are a learning behavior analysis system.
Analyze the provided student chat conversation and extract:
1. "explicit_directives": Specific instructions or rules the student explicitly gave the tutor (e.g., "Use simple explanations", "Stop using analogies", "Give shorter answers").
2. "inferred_traits": Traits, learning preferences, or concepts they are struggling with, inferred from their behavior (e.g., "struggles with recursion", "prefers examples", "learns visually").

You MUST return a JSON object with exactly these two keys: "explicit_directives" and "inferred_traits".
Each key must map to a list of strings.
Do not include any explanation or markdown wrappers. Return ONLY a raw JSON string.
"""

async def analyze_conversation_for_memory(messages: List[Dict[str, str]]) -> Dict[str, List[str]]:
    """
    Sends conversation history to OpenRouter to analyze and extract behavioral directives and traits.
    Returns: {"explicit_directives": [...], "inferred_traits": [...]}
    """
    client = get_openrouter_client()
    
    # Format the conversation history for the analysis LLM
    formatted_convo = ""
    for msg in messages:
        role_label = "Student" if msg.get("role") == "user" else "Tutor"
        formatted_convo += f"{role_label}: {msg.get('content')}\n"
        
    try:
        logger.info("Sending conversation history to OpenRouter for memory analysis...")
        response = await client.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            max_tokens=500,
            messages=[
                {"role": "system", "content": PROFILE_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this conversation:\n\n{formatted_convo}"}
            ]
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Clean any accidental markdown block wrappers from LLM output
        if result_text.startswith("```"):
            lines = result_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            result_text = "\n".join(lines).strip()
            
        parsed = json.loads(result_text)
        logger.info(f"Successfully analyzed conversation. Extracted {len(parsed.get('explicit_directives', []))} directives and {len(parsed.get('inferred_traits', []))} traits.")
        return {
            "explicit_directives": parsed.get("explicit_directives", []),
            "inferred_traits": parsed.get("inferred_traits", [])
        }
    except Exception as e:
        logger.error(f"Failed to analyze conversation: {e}", exc_info=True)
        return {"explicit_directives": [], "inferred_traits": []}

async def extract_explicit_directives(messages: List[Dict[str, str]]) -> List[str]:
    """
    Wrapper function to extract only explicit student directives.
    """
    res = await analyze_conversation_for_memory(messages)
    return res.get("explicit_directives", [])

async def infer_learning_traits(messages: List[Dict[str, str]]) -> List[str]:
    """
    Wrapper function to infer only learning traits/preferences.
    """
    res = await analyze_conversation_for_memory(messages)
    return res.get("inferred_traits", [])
