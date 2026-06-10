from typing import Dict, Any
import logging
from database.supabase import (
    db_create_mastery_record,
    db_get_mastery_record,
    db_update_mastery_score
)

logger = logging.getLogger(__name__)

def get_or_create_mastery(user_id: str, module_id: str) -> Dict[str, Any]:
    """
    Fetches the mastery record for a student and module.
    If none exists, automatically initializes a new record with a score of 0.0.
    """
    logger.info(f"Service: Resolving mastery for user: {user_id}, module: {module_id}")
    record = db_get_mastery_record(user_id, module_id)
    if record is None:
        logger.info(f"Service: No mastery record found. Automatically creating one with default score 0.0")
        record = db_create_mastery_record(user_id, module_id, 0.0)
    return record

def update_mastery(user_id: str, module_id: str, score: float) -> Dict[str, Any]:
    """
    Updates the student's mastery score for a module.
    """
    logger.info(f"Service: Updating mastery for user {user_id}, module {module_id} to {score}")
    # Validate score boundaries
    if score < 0.0 or score > 1.0:
        raise ValueError("Proficiency score must be between 0.0 and 1.0.")
    return db_update_mastery_score(user_id, module_id, score)
