from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from database.supabase import get_supabase_client
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Validates the Supabase JWT token in the Authorization header.
    Returns the user's UUID (as a string) on success.
    Raises 401 Unauthorized on invalid or missing tokens.
    """
    token = credentials.credentials
    try:
        client = get_supabase_client()
        logger.info("Verifying Supabase JWT token...")
        # Verify JWT by fetching the user from Supabase Auth API
        response = client.auth.get_user(token)
        if not response or not response.user:
            logger.warning("Supabase Auth validation failed: User details missing from response.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token."
            )
        user_id = response.user.id
        logger.info(f"Supabase Auth validation succeeded for user_id: {user_id}")
        return user_id
    except Exception as e:
        logger.error(f"JWT verification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials."
        )
