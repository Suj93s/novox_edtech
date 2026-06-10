import asyncio
import logging
from fastapi import BackgroundTasks
from services.chat_service import get_session_messages
from services.profile_analysis import analyze_conversation_for_memory
from services.profile_service import update_behavioral_memory

logger = logging.getLogger(__name__)

async def run_post_chat_analysis_task(session_id: str, user_id: str, retries: int = 3, delay: int = 2) -> None:
    """
    Asynchronous background task that extracts student directives/traits from history
    and updates the profile, implementing retry logic.
    """
    attempt = 0
    while attempt <= retries:
        try:
            logger.info(f"Background Task: Analyzing behavioral memory for session {session_id}, user {user_id} (Attempt {attempt + 1}/{retries + 1})")
            
            # 1. Load conversation history
            history = get_session_messages(session_id)
            if not history:
                logger.warning(f"Background Task: No conversation history found for session {session_id}. Terminating task.")
                return
                
            # 2. Analyze memory
            analysis = await analyze_conversation_for_memory(history)
            new_directives = analysis.get("explicit_directives", [])
            new_traits = analysis.get("inferred_traits", [])
            
            # 3. Update student profile
            if new_directives or new_traits:
                update_behavioral_memory(user_id, new_directives, new_traits)
                logger.info(f"Background Task: Successfully updated student profile for user {user_id}")
            else:
                logger.info("Background Task: No new directives or traits extracted.")
                
            # 4. Prepare future mastery update hooks
            logger.info(f"[Hook] Prepared future mastery updates check for user {user_id} and session {session_id}")
            
            # If we reach here, we succeeded! Break the retry loop.
            return
            
        except Exception as e:
            logger.error(f"Background Task: Attempt {attempt + 1} failed with error: {e}", exc_info=True)
            attempt += 1
            if attempt <= retries:
                backoff = delay * attempt
                logger.info(f"Background Task: Retrying in {backoff} seconds...")
                await asyncio.sleep(backoff)
            else:
                logger.error("Background Task: All retry attempts exhausted. Task failed.")

def queue_analysis_task(background_tasks: BackgroundTasks, session_id: str, user_id: str) -> None:
    """
    Queues the post-chat analysis background task in FastAPI.
    """
    logger.info(f"Queuing post-chat analysis task for session {session_id}, user {user_id}")
    background_tasks.add_task(run_post_chat_analysis_task, session_id, user_id)
