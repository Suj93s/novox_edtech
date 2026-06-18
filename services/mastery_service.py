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

def update_mastery(user_id: str, module_id: str, is_correct: bool) -> Dict[str, Any]:
    """
    Updates the student's mastery score for a module using the 
    Bayesian Knowledge Tracing (BKT) algorithm.
    """
    logger.info(f"Service: Updating mastery for user {user_id}, module {module_id}, correct: {is_correct}")
    
    # Standard BKT Parameters
    P_TRANSITION = 0.1 # Probability of learning the skill
    P_SLIP = 0.1      # Probability of slipping (getting it wrong despite knowing)
    P_GUESS = 0.2     # Probability of guessing (getting it right without knowing)
    
    record = get_or_create_mastery(user_id, module_id)
    current_p_learned = float(record.get('proficiency_score', 0.0))
    
    if is_correct:
        p_correct = current_p_learned * (1 - P_SLIP) + (1 - current_p_learned) * P_GUESS
        p_learned_given_correct = (current_p_learned * (1 - P_SLIP)) / p_correct if p_correct > 0 else 0
        new_p_learned = p_learned_given_correct + (1 - p_learned_given_correct) * P_TRANSITION
    else:
        p_incorrect = current_p_learned * P_SLIP + (1 - current_p_learned) * (1 - P_GUESS)
        p_learned_given_incorrect = (current_p_learned * P_SLIP) / p_incorrect if p_incorrect > 0 else 0
        new_p_learned = p_learned_given_incorrect + (1 - p_learned_given_incorrect) * P_TRANSITION
    
    # Bound the score between 0.0 and 1.0
    new_score = max(0.0, min(1.0, new_p_learned))
    logger.info(f"Service: BKT calculated new proficiency score: {new_score}")
    
    return db_update_mastery_score(user_id, module_id, new_score)
