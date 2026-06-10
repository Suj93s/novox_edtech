import os
import sys

# Add project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from services.curriculum_service import create_module, get_module

def seed():
    course_name = "Advanced Java"
    module_title = "Recursion and Memory"
    concepts = [
        "recursive functions",
        "call stack",
        "base case",
        "memory usage"
    ]
    
    logger.info("Checking if seed data already exists...")
    try:
        existing = get_module(course_name, module_title)
    except Exception as e:
        if "Could not find the table" in str(e):
            logger.error("Seeding failed because database tables are not yet created. Please run schema.sql in Supabase SQL editor first.")
            return
        raise e

    if existing:
        logger.info(f"Seed data already exists (ID: {existing['id']})")
    else:
        logger.info("Inserting seed data...")
        new_module = create_module(course_name, module_title, concepts)
        logger.info(f"Seeded successfully! Module ID: {new_module['id']}")

if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        logger.error(f"Seeding failed: {e}", exc_info=True)
