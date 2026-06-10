from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from models.domain import ChatRequest, ChatResponse
from agents.mentor_agent import process_chat_message
from services.chat_service import (
    create_chat_session,
    get_chat_session,
    save_message,
    get_session_messages
)
from services.profile_service import get_or_create_profile
from services.curriculum_service import get_module, get_module_by_id
from services.mastery_service import get_or_create_mastery
from services.background_processing_service import queue_analysis_task
from services.rag_service import search_relevant_chunks
from services.model_router import route_model
from api.auth import get_current_user_id
import logging

# Set up logging for the endpoint
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)
):
    """
    Main chat endpoint.
    Expects a JSON body with 'message', optional 'session_id',
    and optional curriculum fields ('module_id', 'course_name', 'module_title').
    Enforces JWT authentication and session ownership constraints.
    Returns the generated AI response and the active 'session_id'.
    """
    session_id = request.session_id
    
    try:
        # 1. Validate Session Ownership if session_id is provided
        if session_id:
            logger.info(f"Checking ownership for session: {session_id} by user {user_id}")
            session = get_chat_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found.")
            if str(session.get("user_id")) != user_id:
                logger.warning(f"Unauthorized access attempt by user {user_id} on session {session_id} owned by {session.get('user_id')}")
                raise HTTPException(
                    status_code=403, 
                    detail="Access denied. You do not own this chat session."
                )
        else:
            # 2. Automatically create a new session if session_id is not provided
            logger.info(f"No session_id provided. Creating a new chat session automatically for user {user_id}")
            session_id = create_chat_session(user_id)
            
        # 3. Load or automatically create the student profile
        logger.info(f"Loading student profile for user: {user_id}")
        student_profile = get_or_create_profile(user_id)
        
        # 4. Resolve Curriculum Context (Priority: 1. module_id, 2. course_name + module_title)
        curriculum_context = None
        if request.module_id:
            logger.info(f"Retrieving curriculum module by module_id: {request.module_id}")
            curriculum_context = get_module_by_id(request.module_id)
            if not curriculum_context:
                logger.warning(f"No curriculum module found for ID: {request.module_id}")
        elif request.course_name and request.module_title:
            logger.info(f"Retrieving curriculum module by titles: {request.course_name} - {request.module_title}")
            curriculum_context = get_module(request.course_name, request.module_title)
            if not curriculum_context:
                logger.warning(f"No curriculum module found for course '{request.course_name}' and module '{request.module_title}'")
        
        # 5. Resolve Student Mastery score if curriculum module is loaded
        student_mastery = None
        if curriculum_context:
            module_id = curriculum_context["id"]
            logger.info(f"Loading/Initializing student mastery for user {user_id} and module {module_id}")
            student_mastery = get_or_create_mastery(user_id, module_id)
            
        # 6. Save the user's message to the database
        logger.info(f"Saving user message to session {session_id}")
        save_message(session_id, "user", request.message)
        
        # 7. Retrieve all session messages (history) to pass context to the Mentor AI
        logger.info(f"Retrieving session messages for {session_id} to prepare context.")
        history = get_session_messages(session_id)
        
        # 8. Retrieve relevant document chunks for the user's message
        logger.info(f"Performing document similarity search for query: '{request.message}' by user {user_id}")
        retrieved_chunks = await search_relevant_chunks(request.message, user_id)

        # 9. Classify message and determine targeted LLM via Model Router
        selected_model, category = await route_model(
            message=request.message,
            history=history,
            retrieved_chunks=retrieved_chunks,
            request_override=request.model_override
        )
        logger.info(f"Routed request to model '{selected_model}' based on category '{category}'")

        # 10. Generate the AI response using the agent with full context injections
        logger.info(f"Generating AI response for session {session_id} with context injections.")
        ai_response = await process_chat_message(
            history, 
            student_profile=student_profile,
            curriculum_context=curriculum_context,
            student_mastery=student_mastery,
            retrieved_chunks=retrieved_chunks,
            model_name=selected_model
        )
        
        # 11. Save the AI response to the database
        logger.info(f"Saving AI response to session {session_id}")
        save_message(session_id, "assistant", ai_response)
        
        # 12. Perform Behavioral Memory Analysis asynchronously in the background
        queue_analysis_task(background_tasks, session_id, user_id)
            
        # 13. Return the response model with session_id
        return ChatResponse(response=ai_response, session_id=session_id)
        
    except HTTPException as http_ex:
        # Re-raise HTTPExceptions directly so FastAPI returns correct status codes
        raise http_ex
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        # Check if the error is due to a foreign key violation or invalid session_id
        if "foreign key" in str(e).lower() or "uuid" in str(e).lower():
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid or non-existent session_id: {session_id}"
            )
        raise HTTPException(
            status_code=500, 
            detail="The Mentor AI was unable to process your request. Please try again later."
        )







