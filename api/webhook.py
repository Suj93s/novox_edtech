from fastapi import APIRouter, BackgroundTasks, status, Depends, HTTPException
from models.domain import WebhookAnalyzeRequest
from services.background_processing_service import run_post_chat_analysis_task
from api.auth import get_current_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook/analyze", status_code=status.HTTP_202_ACCEPTED)
async def webhook_analyze(
    request: WebhookAnalyzeRequest, 
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)
):
    """
    Exposed webhook endpoint to manually/externally trigger the behavioral memory analysis
    for a given session and user ID. Enforces authentication and authorization matching.
    """
    if request.user_id != user_id:
        logger.warning(f"Webhook Auth mismatch: Request user_id {request.user_id} does not match token user_id {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access denied. Token user ID does not match request user ID."
        )
        
    logger.info(f"Webhook Triggered: Analyzing memory for session {request.session_id}, user {request.user_id}")
    background_tasks.add_task(run_post_chat_analysis_task, request.session_id, request.user_id)
    return {"status": "Accepted", "message": "Background analysis task queued."}

