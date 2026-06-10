from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import List
from api.auth import get_current_user_id
from models.domain import DocumentIngestionResponse, SearchRequest, SearchResponse, ChunkResult
from services.rag_service import ingest_document, search_relevant_chunks
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentIngestionResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Uploads a document (PDF, TXT, or Markdown), parses it into chunks,
    generates embeddings, and stores them in Supabase.
    Requires JWT authorization.
    """
    logger.info(f"Received file upload request: '{file.filename}' from user '{user_id}'")
    
    # Check file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename."
        )
        
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "txt", "md", "markdown"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: .{ext}. Only PDF, TXT, and Markdown files are supported."
        )
        
    try:
        content = await file.read()
        result = await ingest_document(file.filename, content, user_id)
        
        return DocumentIngestionResponse(
            document_id=result["document_id"],
            document_name=result["document_name"],
            chunk_count=result["chunk_count"]
        )
    except ValueError as val_err:
        logger.warning(f"Validation error during ingestion: {val_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        logger.error(f"Error during document upload/ingestion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}"
        )

@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Performs similarity search on chunks of documents belonging to the authenticated user.
    Requires JWT authorization.
    """
    logger.info(f"Similarity search query received from user '{user_id}' with limit={request.limit}")
    
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty."
        )
        
    try:
        raw_results = await search_relevant_chunks(
            query=request.query,
            user_id=user_id,
            threshold=request.threshold,
            limit=request.limit
        )
        
        # Format database results into domain models
        formatted_results = []
        for r in raw_results:
            formatted_results.append(
                ChunkResult(
                    id=str(r["id"]),
                    document_id=str(r["document_id"]),
                    document_name=r["document_name"],
                    chunk_text=r["chunk_text"],
                    similarity=float(r["similarity"])
                )
            )
            
        return SearchResponse(results=formatted_results)
    except Exception as e:
        logger.error(f"Error performing similarity search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run similarity search."
        )
