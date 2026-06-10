import logging
from core.config import settings
from services.openrouter import get_openrouter_client

logger = logging.getLogger(__name__)

async def classify_via_llm(message: str) -> str:
    """
    Calls OpenRouter using Gemini 2.5 Flash Lite to classify the user's message
    when heuristics are ambiguous.
    """
    try:
        client = get_openrouter_client()
        prompt = (
            "You are an intelligent request classifier for a student learning chatbot. "
            "Your task is to classify the student's query into exactly one of these categories:\n"
            "- simple_question (general explanations, conceptual definitions, greetings, simple questions)\n"
            "- coding_question (requests to write code, design algorithms, syntax help, or code structure)\n"
            "- debugging_question (fixing stack traces, errors, compile/runtime exceptions, or diagnosing bugs)\n"
            "- document_heavy_question (questions asking about specific documents, files, or custom context)\n\n"
            f"Student Message: \"{message}\"\n\n"
            "Output only the category name (simple_question, coding_question, debugging_question, or document_heavy_question) "
            "and absolutely nothing else."
        )
        
        logger.info("Executing LLM-based classification fallback via OpenRouter...")
        response = await client.chat.completions.create(
            model=settings.MODEL_FLASH_LITE,
            max_tokens=20,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result_text = response.choices[0].message.content.strip().lower()
        # Clean any quotes or formatting
        result_text = result_text.replace("`", "").replace("'", "").replace("\"", "")
        
        valid_categories = ["simple_question", "coding_question", "debugging_question", "document_heavy_question"]
        for cat in valid_categories:
            if cat in result_text:
                logger.info(f"LLM classified request category as: {cat}")
                return cat
                
        logger.warning(f"LLM returned unrecognized classification category: '{result_text}'. Defaulting to 'simple_question'.")
        return "simple_question"
    except Exception as e:
        logger.error(f"Error in LLM classification fallback: {e}", exc_info=True)
        return "simple_question"

def classify_via_heuristics(message: str, retrieved_chunks: list = None) -> str:
    """
    Runs quick, zero-cost heuristic checks to classify the message.
    Returns the category name if matched, or None if ambiguous.
    """
    # 1. Document Heavy Heuristics
    if retrieved_chunks:
        total_chars = sum(len(c.get("chunk_text", "")) for c in retrieved_chunks)
        if total_chars > 1500:
            logger.info(f"Heuristics match: 'document_heavy_question' due to chunks length ({total_chars} chars)")
            return "document_heavy_question"
            
    message_lower = message.lower()
    
    # Check for code blocks
    has_code_block = "```" in message
    
    # 2. Debugging Heuristics
    debugging_keywords = [
        "error", "exception", "bug", "traceback", "stacktrace", 
        "compile error", "runtime error", "crash", "fails", "fail", 
        "unexpected behavior", "doesn't work", "broken"
    ]
    if has_code_block and any(kw in message_lower for kw in debugging_keywords):
        logger.info("Heuristics match: 'debugging_question' due to code block + debugging keyword.")
        return "debugging_question"
        
    # 3. Coding Heuristics
    coding_keywords = [
        "write a function", "write a class", "implement", "code", "syntax", 
        "algorithm", "recursion", "array", "pointer", "variable", "loop", 
        "function", "class", "method"
    ]
    if has_code_block or any(kw in message_lower for kw in coding_keywords):
        logger.info("Heuristics match: 'coding_question' due to programming keyword/code block.")
        return "coding_question"
        
    return None

async def classify_request(message: str, history: list = None, retrieved_chunks: list = None) -> str:
    """
    Classifies a request into one of: simple_question, coding_question, debugging_question, document_heavy_question.
    Combines fast heuristics with an LLM fallback.
    """
    # 1. Attempt heuristic match
    category = classify_via_heuristics(message, retrieved_chunks)
    if category:
        return category
        
    # 2. Fall back to LLM-based classifier
    return await classify_via_llm(message)

async def route_model(
    message: str,
    history: list = None,
    retrieved_chunks: list = None,
    request_override: str = None
) -> tuple[str, str]:
    """
    Determines which model to use based on override params or intelligent classification.
    Returns:
        tuple[str, str]: (selected_model, category_name)
    """
    # 1. Manual Request-Level Override
    if request_override:
        logger.info(f"Model routing override via request parameter: '{request_override}'")
        return request_override, "manual_override"
        
    # 2. Environment-Level Override
    if settings.MODEL_OVERRIDE:
        logger.info(f"Model routing override via environment setting: '{settings.MODEL_OVERRIDE}'")
        return settings.MODEL_OVERRIDE, "env_override"
        
    # 3. Intelligent Classification
    category = await classify_request(message, history, retrieved_chunks)
    
    # 4. Map Category to Model Config
    if category == "debugging_question":
        selected_model = settings.ROUTE_DEBUGGING_QUESTION
    elif category == "coding_question":
        selected_model = settings.ROUTE_CODING_QUESTION
    elif category == "document_heavy_question":
        selected_model = settings.ROUTE_DOCUMENT_HEAVY_QUESTION
    else:
        selected_model = settings.ROUTE_SIMPLE_QUESTION
        
    logger.info(f"Routing request to model '{selected_model}' based on category '{category}'")
    return selected_model, category
