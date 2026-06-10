from prompts.mentor_prompts import MENTOR_SYSTEM_PROMPT
from services.openrouter import get_openrouter_client
from core.config import settings
import logging

# Set up logging for error handling
logger = logging.getLogger(__name__)

async def process_chat_message(
    messages_history: list, 
    student_profile: dict = None,
    curriculum_context: dict = None,
    student_mastery: dict = None,
    retrieved_chunks: list = None,
    model_name: str = None
) -> str:
    """
    This function acts as our Antigravity Mentor Agent.
    It takes the list of past messages (including the new user message),
    adds our system persona (and optional profile, curriculum, and mastery context), and sends it to OpenRouter.
    """
    # 1. Get our connected OpenRouter client
    client = get_openrouter_client()
    
    # 2. Load and resolve guardrail configurations
    guardrails_enabled = getattr(settings, "GUARDRAILS_ENABLED", True)
    socratic_strictness = getattr(settings, "SOCRATIC_STRICTNESS", "strict")
    
    if student_profile and isinstance(student_profile.get("system_metadata"), dict):
        metadata = student_profile["system_metadata"]
        if "guardrails_enabled" in metadata:
            guardrails_enabled = bool(metadata["guardrails_enabled"])
        if "socratic_strictness" in metadata:
            socratic_strictness = str(metadata["socratic_strictness"])

    # 3. Analyze the latest user message for guardrail validation
    latest_user_message = ""
    for msg in reversed(messages_history):
        if msg.get("role") == "user":
            latest_user_message = msg.get("content", "")
            break

    guardrail_directive = ""
    if guardrails_enabled:
        solution_keywords = [
            "give me the answer", "write the code", "do it for me", 
            "give me the solution", "solve it for me", "solve this",
            "show me the code", "provide the code", "write it for me",
            "just give me the code", "what is the code", "code please"
        ]
        msg_lower = latest_user_message.lower()
        is_solution_request = any(kw in msg_lower for kw in solution_keywords)

        definition_keywords = ["what is", "define", "what does", "meaning of", "explain the term", "definition of"]
        is_definition = any(kw in msg_lower for kw in definition_keywords) and "?" in msg_lower
        
        theory_keywords = ["how does", "why is", "explain how", "explain why", "difference between", "how JVM", "how garbage collection", "in theory"]
        is_theory = any(kw in msg_lower for kw in theory_keywords)
        
        is_exception = is_definition or is_theory
        
        if is_solution_request:
            if socratic_strictness == "strict":
                guardrail_directive = (
                    "\n\n### CRITICAL GUARDRAIL TRIGGERED: DIRECT ANSWER REQUEST DETECTED\n"
                    "The student is asking you to write the code or provide the direct solution. "
                    "You MUST refuse politely but firmly. Remind them of your role as a Socratic guide, "
                    "then validate their effort, give a high-level conceptual hint, and ask a leading question. "
                    "Do not dump the code!"
                )
            else:
                guardrail_directive = (
                    "\n\n### SOCRATIC INSTRUCTION: SOLUTION REQUEST DETECTED\n"
                    "The student is asking for an answer. Avoid giving the direct solution, but guide them using the Socratic method."
                )
        elif is_exception:
            guardrail_directive = (
                "\n\n### SOCRATIC INSTRUCTION: EXCEPTION CASE ACTIVE\n"
                "This request is classified as a Definition/Theory/General Discussion question. "
                "You are ALLOWED to provide a direct answer, explanation, or definition here without withholding information. "
                "You do not need to follow the 3-step Socratic method for definitions and general conceptual descriptions, but remain pedagogical."
            )
        else:
            # Standard Socratic instruction enforcement
            guardrail_directive = (
                "\n\n### SOCRATIC INSTRUCTION: ACTIVE SOCRATIC TUTORING\n"
                "Ensure your response strictly follows the 3-step format:\n"
                "Step 1: Validate Effort (Acknowledge and encourage their thinking/attempt).\n"
                "Step 2: Conceptual Hint (Provide a high-level theoretical hint, avoiding solutions/code).\n"
                "Step 3: Leading Question (Ask a single, focused question directing them to the next small step)."
            )

    try:
        # Construct system prompt, injecting profile context if present
        system_prompt = MENTOR_SYSTEM_PROMPT
        if student_profile:
            behavioral_chart = student_profile.get("behavioral_chart", {})
            directives = behavioral_chart.get("explicit_directives", [])
            traits = behavioral_chart.get("inferred_traits", [])
            
            profile_context = "\n\n### STUDENT PROFILE CONTEXT\n"
            profile_context += f"Student User ID: {student_profile.get('user_id')}\n"
            
            if directives:
                profile_context += "Explicit Directives (follow these guidelines strictly):\n"
                for directive in directives:
                    profile_context += f"- {directive}\n"
            else:
                profile_context += "Explicit Directives: None specified.\n"
                
            if traits:
                profile_context += "Inferred Traits/Preferences:\n"
                for trait in traits:
                    profile_context += f"- {trait}\n"
            else:
                profile_context += "Inferred Traits/Preferences: None detected.\n"
                
            system_prompt += profile_context
            logger.info("Successfully injected student profile context into system prompt.")
            
        # Inject curriculum context if present
        if curriculum_context:
            course = curriculum_context.get("course_name")
            module = curriculum_context.get("module_title")
            concepts = curriculum_context.get("concepts", [])
            
            curriculum_str = "\n\n### ACTIVE CURRICULUM CONTEXT\n"
            curriculum_str += f"Active Course: {course}\n"
            curriculum_str += f"Current Module: {module}\n"
            
            if concepts:
                curriculum_str += "Target Concepts to Teach/Reinforce:\n"
                for concept in concepts:
                    curriculum_str += f"- {concept}\n"
            else:
                curriculum_str += "Target Concepts: None specified.\n"
                
            system_prompt += curriculum_str
            logger.info("Successfully injected curriculum context into system prompt.")
            
        # Inject student mastery if present
        if student_mastery:
            score = float(student_mastery.get("proficiency_score", 0.0))
            
            mastery_str = "\n\n### STUDENT MASTERY / PROFICIENCY\n"
            mastery_str += f"Current Proficiency Score in this Module: {score:.2f} (scale 0.0 to 1.0)\n"
            
            if score < 0.3:
                mastery_str += "Instructional Guideline: The student has beginner proficiency. Explain concepts using basic terms, simple step-by-step logic, and friendly real-world analogies. Avoid overly academic or advanced terminology.\n"
            elif score < 0.7:
                mastery_str += "Instructional Guideline: The student has intermediate proficiency. Build on core fundamentals, explain medium-difficulty ideas clearly, and introduce technical terms with short definitions.\n"
            else:
                mastery_str += "Instructional Guideline: The student has advanced proficiency. Use professional/academic terminology, present challenging concepts, and guide them with high-level conceptual questions rather than basic review.\n"
                
            system_prompt += mastery_str
            logger.info(f"Successfully injected student mastery context (score: {score}) into system prompt.")
            
        # Inject retrieved document context if present
        if retrieved_chunks:
            rag_str = "\n\n### RETRIEVED DOCUMENT CONTEXT\n"
            rag_str += "Use the following factual passages to inform your explanations and answer the student's questions. Rely ONLY on the provided context if specified. Cite the document names if relevant:\n"
            for chunk in retrieved_chunks:
                doc_name = chunk.get("document_name", "Unknown Document")
                text = chunk.get("chunk_text", "")
                rag_str += f"--- Document: {doc_name} ---\n{text}\n"
            rag_str += "--------------------\n"
            system_prompt += rag_str
            logger.info(f"Successfully injected {len(retrieved_chunks)} retrieved document chunks into system prompt.")
            
        # Inject guardrail directive if active
        if guardrail_directive:
            system_prompt += guardrail_directive
            logger.info("Successfully injected guardrail directive into system prompt.")
            
        # 2. Construct messages list with system prompt followed by history
        messages = [{"role": "system", "content": system_prompt}]
        for msg in messages_history:
            # We map database role to what OpenRouter API expects if they match.
            # Role values are 'user' and 'assistant'. OpenRouter accepts 'user' and 'assistant' (or 'system').
            messages.append({
                "role": msg.get("role"),
                "content": msg.get("content")
            })
            
        # 3. Make the request to OpenRouter using the selected model name
        target_model = model_name or settings.MODEL_FLASH_LITE
        logger.info(f"Sending request to OpenRouter with {len(messages)} messages (including system prompt) using model '{target_model}'.")
        response = await client.chat.completions.create(
            model=target_model,
            max_tokens=1000,
            messages=messages
        )
        
        # 4. Extract and return the AI's text response
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error in mentor agent: {e}", exc_info=True)
        raise RuntimeError("Failed to generate AI response.")

async def process_chat_message_stream(
    messages_history: list, 
    student_profile: dict = None,
    curriculum_context: dict = None,
    student_mastery: dict = None,
    retrieved_chunks: list = None,
    model_name: str = None
):
    """
    This function processes the student message and returns an async generator 
    yielding AI response tokens step-by-step from OpenRouter.
    """
    client = get_openrouter_client()
    
    # 2. Load and resolve guardrail configurations
    guardrails_enabled = getattr(settings, "GUARDRAILS_ENABLED", True)
    socratic_strictness = getattr(settings, "SOCRATIC_STRICTNESS", "strict")
    
    if student_profile and isinstance(student_profile.get("system_metadata"), dict):
        metadata = student_profile["system_metadata"]
        if "guardrails_enabled" in metadata:
            guardrails_enabled = bool(metadata["guardrails_enabled"])
        if "socratic_strictness" in metadata:
            socratic_strictness = str(metadata["socratic_strictness"])

    # 3. Analyze the latest user message for guardrail validation
    latest_user_message = ""
    for msg in reversed(messages_history):
        if msg.get("role") == "user":
            latest_user_message = msg.get("content", "")
            break

    guardrail_directive = ""
    if guardrails_enabled:
        solution_keywords = [
            "give me the answer", "write the code", "do it for me", 
            "give me the solution", "solve it for me", "solve this",
            "show me the code", "provide the code", "write it for me",
            "just give me the code", "what is the code", "code please"
        ]
        msg_lower = latest_user_message.lower()
        is_solution_request = any(kw in msg_lower for kw in solution_keywords)

        definition_keywords = ["what is", "define", "what does", "meaning of", "explain the term", "definition of"]
        is_definition = any(kw in msg_lower for kw in definition_keywords) and "?" in msg_lower
        
        theory_keywords = ["how does", "why is", "explain how", "explain why", "difference between", "how JVM", "how garbage collection", "in theory"]
        is_theory = any(kw in msg_lower for kw in theory_keywords)
        
        is_exception = is_definition or is_theory
        
        if is_solution_request:
            if socratic_strictness == "strict":
                guardrail_directive = (
                    "\n\n### CRITICAL GUARDRAIL TRIGGERED: DIRECT ANSWER REQUEST DETECTED\n"
                    "The student is asking you to write the code or provide the direct solution. "
                    "You MUST refuse politely but firmly. Remind them of your role as a Socratic guide, "
                    "then validate their effort, give a high-level conceptual hint, and ask a leading question. "
                    "Do not dump the code!"
                )
            else:
                guardrail_directive = (
                    "\n\n### SOCRATIC INSTRUCTION: SOLUTION REQUEST DETECTED\n"
                    "The student is asking for an answer. Avoid giving the direct solution, but guide them using the Socratic method."
                )
        elif is_exception:
            guardrail_directive = (
                "\n\n### SOCRATIC INSTRUCTION: EXCEPTION CASE ACTIVE\n"
                "This request is classified as a Definition/Theory/General Discussion question. "
                "You are ALLOWED to provide a direct answer, explanation, or definition here without withholding information. "
                "You do not need to follow the 3-step Socratic method for definitions and general conceptual descriptions, but remain pedagogical."
            )
        else:
            # Standard Socratic instruction enforcement
            guardrail_directive = (
                "\n\n### SOCRATIC INSTRUCTION: ACTIVE SOCRATIC TUTORING\n"
                "Ensure your response strictly follows the 3-step format:\n"
                "Step 1: Validate Effort (Acknowledge and encourage their thinking/attempt).\n"
                "Step 2: Conceptual Hint (Provide a high-level theoretical hint, avoiding solutions/code).\n"
                "Step 3: Leading Question (Ask a single, focused question directing them to the next small step)."
            )

    try:
        # Construct system prompt, injecting profile context if present
        system_prompt = MENTOR_SYSTEM_PROMPT
        if student_profile:
            behavioral_chart = student_profile.get("behavioral_chart", {})
            directives = behavioral_chart.get("explicit_directives", [])
            traits = behavioral_chart.get("inferred_traits", [])
            
            profile_context = "\n\n### STUDENT PROFILE CONTEXT\n"
            profile_context += f"Student User ID: {student_profile.get('user_id')}\n"
            
            if directives:
                profile_context += "Explicit Directives (follow these guidelines strictly):\n"
                for directive in directives:
                    profile_context += f"- {directive}\n"
            else:
                profile_context += "Explicit Directives: None specified.\n"
                
            if traits:
                profile_context += "Inferred Traits/Preferences:\n"
                for trait in traits:
                    profile_context += f"- {trait}\n"
            else:
                profile_context += "Inferred Traits/Preferences: None detected.\n"
                
            system_prompt += profile_context
            logger.info("Successfully injected student profile context into system prompt.")
            
        # Inject curriculum context if present
        if curriculum_context:
            course = curriculum_context.get("course_name")
            module = curriculum_context.get("module_title")
            concepts = curriculum_context.get("concepts", [])
            
            curriculum_str = "\n\n### ACTIVE CURRICULUM CONTEXT\n"
            curriculum_str += f"Active Course: {course}\n"
            curriculum_str += f"Current Module: {module}\n"
            
            if concepts:
                curriculum_str += "Target Concepts to Teach/Reinforce:\n"
                for concept in concepts:
                    curriculum_str += f"- {concept}\n"
            else:
                curriculum_str += "Target Concepts: None specified.\n"
                
            system_prompt += curriculum_str
            logger.info("Successfully injected curriculum context into system prompt.")
            
        # Inject student mastery if present
        if student_mastery:
            score = float(student_mastery.get("proficiency_score", 0.0))
            
            mastery_str = "\n\n### STUDENT MASTERY / PROFICIENCY\n"
            mastery_str += f"Current Proficiency Score in this Module: {score:.2f} (scale 0.0 to 1.0)\n"
            
            if score < 0.3:
                mastery_str += "Instructional Guideline: The student has beginner proficiency. Explain concepts using basic terms, simple step-by-step logic, and friendly real-world analogies. Avoid overly academic or advanced terminology.\n"
            elif score < 0.7:
                mastery_str += "Instructional Guideline: The student has intermediate proficiency. Build on core fundamentals, explain medium-difficulty ideas clearly, and introduce technical terms with short definitions.\n"
            else:
                mastery_str += "Instructional Guideline: The student has advanced proficiency. Use professional/academic terminology, present challenging concepts, and guide them with high-level conceptual questions rather than basic review.\n"
                
            system_prompt += mastery_str
            logger.info(f"Successfully injected student mastery context (score: {score}) into system prompt.")
            
        # Inject retrieved document context if present
        if retrieved_chunks:
            rag_str = "\n\n### RETRIEVED DOCUMENT CONTEXT\n"
            rag_str += "Use the following factual passages to inform your explanations and answer the student's questions. Rely ONLY on the provided context if specified. Cite the document names if relevant:\n"
            for chunk in retrieved_chunks:
                doc_name = chunk.get("document_name", "Unknown Document")
                text = chunk.get("chunk_text", "")
                rag_str += f"--- Document: {doc_name} ---\n{text}\n"
            rag_str += "--------------------\n"
            system_prompt += rag_str
            logger.info(f"Successfully injected {len(retrieved_chunks)} retrieved document chunks into system prompt.")
            
        # Inject guardrail directive if active
        if guardrail_directive:
            system_prompt += guardrail_directive
            logger.info("Successfully injected guardrail directive into system prompt.")
            
        # 2. Construct messages list with system prompt followed by history
        messages = [{"role": "system", "content": system_prompt}]
        for msg in messages_history:
            messages.append({
                "role": msg.get("role"),
                "content": msg.get("content")
            })
            
        # 3. Make the streaming request to OpenRouter using the selected model name
        target_model = model_name or settings.MODEL_FLASH_LITE
        logger.info(f"Sending streaming request to OpenRouter with {len(messages)} messages using model '{target_model}'.")
        
        response_stream = await client.chat.completions.create(
            model=target_model,
            max_tokens=1000,
            messages=messages,
            stream=True
        )
        
        async for chunk in response_stream:
            if chunk.choices:
                token = chunk.choices[0].delta.content or ""
                if token:
                    yield token
                    
    except Exception as e:
        logger.error(f"Error in streaming mentor agent: {e}", exc_info=True)
        yield "An error occurred while streaming response. Please try again."




