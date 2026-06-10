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




