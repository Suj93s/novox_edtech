from typing import List, Dict, Any
import logging
from database.supabase import (
    db_create_chat_session,
    db_get_chat_session,
    db_save_message,
    db_get_session_messages
)

logger = logging.getLogger(__name__)

def create_chat_session(user_id: str) -> str:
    """
    Creates a new chat session and returns the generated session ID (UUID).
    """
    logger.info(f"Service: Creating a new chat session for user {user_id}")
    session = db_create_chat_session(user_id)
    return session["id"]

def get_chat_session(session_id: str) -> Dict[str, Any]:
    """
    Retrieves the chat session details by ID.
    """
    logger.info(f"Service: Retrieving chat session details for ID {session_id}")
    return db_get_chat_session(session_id)


def save_message(session_id: str, role: str, content: str) -> Dict[str, Any]:
    """
    Saves a message (either user or assistant) linked to a session ID.
    """
    logger.info(f"Service: Saving message for session {session_id} with role {role}")
    return db_save_message(session_id, role, content)

def get_session_messages(session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all messages for a given session ID.
    """
    logger.info(f"Service: Retrieving history for session {session_id}")
    return db_get_session_messages(session_id)
