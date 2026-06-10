from typing import Dict, Any
import logging
from database.supabase import (
    db_create_student_profile,
    db_get_student_profile,
    db_update_student_profile
)

logger = logging.getLogger(__name__)

def get_or_create_profile(user_id: str) -> Dict[str, Any]:
    """
    Fetches the profile for user_id. If none exists, creates it automatically with defaults.
    """
    logger.info(f"Service: Getting profile for user_id: {user_id}")
    profile = db_get_student_profile(user_id)
    if profile is None:
        logger.info(f"Service: No profile found for user_id: {user_id}. Creating new profile automatically.")
        # Default behavioral_chart structure
        default_chart = {
            "explicit_directives": [],
            "inferred_traits": []
        }
        profile = db_create_student_profile(user_id, behavioral_chart=default_chart, system_metadata={})
    return profile

def update_profile(user_id: str, behavioral_chart: dict = None, system_metadata: dict = None) -> Dict[str, Any]:
    """
    Updates the student profile details.
    """
    logger.info(f"Service: Updating profile for user_id: {user_id}")
    return db_update_student_profile(user_id, behavioral_chart, system_metadata)

def update_behavioral_memory(user_id: str, new_directives: list, new_traits: list) -> Dict[str, Any]:
    """
    Merges and deduplicates new directives and traits with the student's profile in Supabase.
    """
    logger.info(f"Service: Updating behavioral memory for user_id: {user_id}")
    profile = get_or_create_profile(user_id)
    chart = profile.get("behavioral_chart", {})
    if not isinstance(chart, dict):
        chart = {}
        
    existing_directives = chart.get("explicit_directives", [])
    existing_traits = chart.get("inferred_traits", [])
    
    # Helper to merge items case-insensitively while preserving original casing of first added
    def merge_lists(existing: list, new_items: list) -> list:
        seen = {item.strip().lower() for item in existing if item and item.strip()}
        merged = list(existing)
        for item in new_items:
            if not item:
                continue
            cleaned = item.strip()
            if cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                merged.append(cleaned)
        return merged
        
    updated_directives = merge_lists(existing_directives, new_directives)
    updated_traits = merge_lists(existing_traits, new_traits)
    
    updated_chart = {
        "explicit_directives": updated_directives,
        "inferred_traits": updated_traits
    }
    
    return db_update_student_profile(user_id, behavioral_chart=updated_chart)

