from supabase import create_client, Client
from core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """Returns a Supabase client instance."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise ValueError("Supabase credentials are not set in environment variables.")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

def db_create_chat_session(user_id: str) -> dict:
    """
    Creates a new chat session in Supabase and returns the created session data.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Creating a new chat session in Supabase for user {user_id}")
        response = client.table("chat_sessions").insert({"user_id": user_id}).execute()
        
        if not response.data:
            raise RuntimeError("No data returned from chat_sessions insert.")
            
        session = response.data[0]
        logger.info(f"Successfully created chat session with ID: {session.get('id')} for user {user_id}")
        return session
    except Exception as e:
        logger.error(f"Error creating chat session in DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while creating chat session: {e}")

def db_get_chat_session(session_id: str) -> dict:
    """
    Retrieves a chat session by ID.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Retrieving chat session details for ID: {session_id}")
        response = client.table("chat_sessions").select("*").eq("id", session_id).execute()
        if not response.data:
            return None
        return response.data[0]
    except Exception as e:
        logger.error(f"Error retrieving chat session from DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while fetching chat session: {e}")


def db_save_message(session_id: str, role: str, content: str) -> dict:
    """
    Saves a chat message linked to a session_id in Supabase.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Saving message for session {session_id} with role '{role}'")
        
        message_data = {
            "session_id": session_id,
            "role": role,
            "content": content
        }
        
        response = client.table("chat_messages").insert(message_data).execute()
        
        if not response.data:
            raise RuntimeError("No data returned from chat_messages insert.")
            
        saved_msg = response.data[0]
        logger.info(f"Successfully saved message with ID: {saved_msg.get('id')} to session {session_id}")
        return saved_msg
    except Exception as e:
        logger.error(f"Error saving message to DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while saving message: {e}")

def db_get_session_messages(session_id: str) -> list:
    """
    Retrieves all messages for a session ordered by creation time (ascending).
    """
    try:
        client = get_supabase_client()
        logger.info(f"Retrieving all messages for session {session_id}")
        
        response = client.table("chat_messages") \
            .select("*") \
            .eq("session_id", session_id) \
            .order("created_at", desc=False) \
            .execute()
            
        logger.info(f"Retrieved {len(response.data)} messages for session {session_id}")
        return response.data
    except Exception as e:
        logger.error(f"Error retrieving session messages from DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while fetching session history: {e}")

def db_create_student_profile(user_id: str, behavioral_chart: dict = None, system_metadata: dict = None) -> dict:
    """
    Creates a new student profile in Supabase and returns the created profile data.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Creating a new student profile for user_id: {user_id}")
        profile_data = {"user_id": user_id}
        if behavioral_chart is not None:
            profile_data["behavioral_chart"] = behavioral_chart
        if system_metadata is not None:
            profile_data["system_metadata"] = system_metadata
            
        response = client.table("student_profiles").insert(profile_data).execute()
        if not response.data:
            raise RuntimeError("No data returned from student_profiles insert.")
        profile = response.data[0]
        logger.info(f"Successfully created student profile with ID: {profile.get('id')} for user_id: {user_id}")
        return profile
    except Exception as e:
        logger.error(f"Error creating student profile in DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while creating student profile: {e}")

def db_get_student_profile(user_id: str) -> dict:
    """
    Retrieves the student profile for user_id. Returns None if not found.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Retrieving student profile for user_id: {user_id}")
        response = client.table("student_profiles").select("*").eq("user_id", user_id).execute()
        if not response.data:
            return None
        return response.data[0]
    except Exception as e:
        logger.error(f"Error retrieving student profile from DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while fetching student profile: {e}")

def db_update_student_profile(user_id: str, behavioral_chart: dict = None, system_metadata: dict = None) -> dict:
    """
    Updates the student profile for user_id and returns the updated profile data.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Updating student profile for user_id: {user_id}")
        update_data = {}
        if behavioral_chart is not None:
            update_data["behavioral_chart"] = behavioral_chart
        if system_metadata is not None:
            update_data["system_metadata"] = system_metadata
            
        if not update_data:
            raise ValueError("No fields provided to update.")
            
        response = client.table("student_profiles").update(update_data).eq("user_id", user_id).execute()
        if not response.data:
            raise RuntimeError("No data returned from student_profiles update.")
        profile = response.data[0]
        logger.info(f"Successfully updated student profile for user_id: {user_id}")
        return profile
    except Exception as e:
        logger.error(f"Error updating student profile in DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while updating student profile: {e}")

def db_create_curriculum_module(course_name: str, module_title: str, concepts: list) -> dict:
    """
    Creates a new curriculum module in Supabase.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Creating curriculum module: {course_name} - {module_title}")
        module_data = {
            "course_name": course_name,
            "module_title": module_title,
            "concepts": concepts
        }
        response = client.table("novox_curriculum").insert(module_data).execute()
        if not response.data:
            raise RuntimeError("No data returned from novox_curriculum insert.")
        module = response.data[0]
        logger.info(f"Successfully created curriculum module ID: {module.get('id')}")
        return module
    except Exception as e:
        logger.error(f"Error creating curriculum module in DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while creating curriculum module: {e}")

def db_get_curriculum_module(course_name: str, module_title: str) -> dict:
    """
    Retrieves a curriculum module by course name and module title.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Retrieving curriculum module: {course_name} - {module_title}")
        response = client.table("novox_curriculum") \
            .select("*") \
            .eq("course_name", course_name) \
            .eq("module_title", module_title) \
            .execute()
        if not response.data:
            return None
        return response.data[0]
    except Exception as e:
        logger.error(f"Error retrieving curriculum module from DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while fetching curriculum module: {e}")

def db_get_curriculum_module_by_id(module_id: str) -> dict:
    """
    Retrieves a curriculum module by its UUID.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Retrieving curriculum module by ID: {module_id}")
        response = client.table("novox_curriculum") \
            .select("*") \
            .eq("id", module_id) \
            .execute()
        if not response.data:
            return None
        return response.data[0]
    except Exception as e:
        logger.error(f"Error retrieving curriculum module by ID from DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while fetching curriculum module by ID: {e}")

def db_list_curriculum_modules(course_name: str = None) -> list:
    """
    Lists curriculum modules. Optionally filtered by course_name.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Listing curriculum modules (filter course: {course_name})")
        query = client.table("novox_curriculum").select("*")
        if course_name:
            query = query.eq("course_name", course_name)
        response = query.execute()
        return response.data
    except Exception as e:
        logger.error(f"Error listing curriculum modules from DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while listing curriculum modules: {e}")

def db_update_curriculum_module(module_id: str, concepts: list) -> dict:
    """
    Updates the concepts array of an existing curriculum module.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Updating concepts for curriculum module ID: {module_id}")
        response = client.table("novox_curriculum") \
            .update({"concepts": concepts}) \
            .eq("id", module_id) \
            .execute()
        if not response.data:
            raise RuntimeError("No data returned from novox_curriculum update.")
        return response.data[0]
    except Exception as e:
        logger.error(f"Error updating curriculum module in DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while updating curriculum module: {e}")

def db_create_mastery_record(user_id: str, module_id: str, proficiency_score: float = 0.0) -> dict:
    """
    Creates a new student mastery record in Supabase.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Creating mastery record for user {user_id} and module {module_id}")
        mastery_data = {
            "user_id": user_id,
            "module_id": module_id,
            "proficiency_score": proficiency_score
        }
        response = client.table("student_mastery").insert(mastery_data).execute()
        if not response.data:
            raise RuntimeError("No data returned from student_mastery insert.")
        return response.data[0]
    except Exception as e:
        logger.error(f"Error creating student mastery in DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while creating student mastery: {e}")

def db_get_mastery_record(user_id: str, module_id: str) -> dict:
    """
    Retrieves a student's mastery record for a specific curriculum module.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Retrieving mastery record for user {user_id} and module {module_id}")
        response = client.table("student_mastery") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("module_id", module_id) \
            .execute()
        if not response.data:
            return None
        return response.data[0]
    except Exception as e:
        logger.error(f"Error retrieving student mastery from DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while fetching student mastery: {e}")

def db_update_mastery_score(user_id: str, module_id: str, score: float) -> dict:
    """
    Updates the proficiency score for a student's mastery record.
    """
    try:
        client = get_supabase_client()
        logger.info(f"Updating mastery score to {score} for user {user_id} and module {module_id}")
        response = client.table("student_mastery") \
            .update({"proficiency_score": score, "updated_at": "now()"}) \
            .eq("user_id", user_id) \
            .eq("module_id", module_id) \
            .execute()
        if not response.data:
            raise RuntimeError("No data returned from student_mastery update.")
        return response.data[0]
    except Exception as e:
        logger.error(f"Error updating student mastery in DB: {e}", exc_info=True)
        raise RuntimeError(f"Database error while updating student mastery: {e}")




