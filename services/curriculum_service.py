from typing import List, Dict, Any, Optional
import logging
from database.supabase import (
    db_create_curriculum_module,
    db_get_curriculum_module,
    db_get_curriculum_module_by_id,
    db_list_curriculum_modules,
    db_update_curriculum_module
)

logger = logging.getLogger(__name__)

def create_module(course_name: str, module_title: str, concepts: List[str]) -> Dict[str, Any]:
    """
    Service to create a new curriculum module.
    """
    logger.info(f"Service: Creating curriculum module {course_name} - {module_title}")
    return db_create_curriculum_module(course_name, module_title, concepts)

def get_module(course_name: str, module_title: str) -> Optional[Dict[str, Any]]:
    """
    Service to fetch a curriculum module by course name and module title.
    """
    logger.info(f"Service: Fetching curriculum module by title {course_name} - {module_title}")
    return db_get_curriculum_module(course_name, module_title)

def get_module_by_id(module_id: str) -> Optional[Dict[str, Any]]:
    """
    Service to fetch a curriculum module by its UUID.
    """
    logger.info(f"Service: Fetching curriculum module by ID: {module_id}")
    return db_get_curriculum_module_by_id(module_id)

def list_modules(course_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Service to list modules, optionally filtered by course name.
    """
    logger.info(f"Service: Listing curriculum modules (course: {course_name})")
    return db_list_curriculum_modules(course_name)

def update_module(module_id: str, concepts: List[str]) -> Dict[str, Any]:
    """
    Service to update concepts for an existing module.
    """
    logger.info(f"Service: Updating module concepts for ID: {module_id}")
    return db_update_curriculum_module(module_id, concepts)
