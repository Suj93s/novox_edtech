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
    modules_to_seed = [
        {
            "course_name": "Development",
            "module_title": "Development Master Track",
            "concepts": ["react", "flutter", "python", "mern", "system design"]
        },
        {
            "course_name": "Design",
            "module_title": "Design Master Track",
            "concepts": ["ui/ux", "graphic design", "video editing", "figma"]
        },
        {
            "course_name": "Marketing",
            "module_title": "Marketing Master Track",
            "concepts": ["seo", "paid ads", "social media", "analytics"]
        }
    ]
    
    logger.info("Checking if database tables exist...")
    try:
        # Probe database availability using the first module
        get_module(modules_to_seed[0]["course_name"], modules_to_seed[0]["module_title"])
    except Exception as e:
        if "Could not find the table" in str(e):
            logger.error("Seeding failed because database tables are not yet created. Please run schema.sql in Supabase SQL editor first.")
            return
        raise e

    for mod in modules_to_seed:
        existing = get_module(mod["course_name"], mod["module_title"])
        if existing:
            logger.info(f"Seed data already exists for {mod['course_name']} - {mod['module_title']} (ID: {existing['id']})")
        else:
            logger.info(f"Inserting seed data for {mod['course_name']} - {mod['module_title']}...")
            new_module = create_module(mod["course_name"], mod["module_title"], mod["concepts"])
            logger.info(f"Seeded successfully! Module ID: {new_module['id']}")

if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        logger.error(f"Seeding failed: {e}", exc_info=True)
