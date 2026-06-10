from pydantic import BaseModel
from typing import List, Optional

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    course_name: Optional[str] = None
    module_title: Optional[str] = None
    module_id: Optional[str] = None
    model_override: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

class CurriculumModuleCreate(BaseModel):
    course_name: str
    module_title: str
    concepts: List[str]

class CurriculumModuleResponse(BaseModel):
    id: str
    course_name: str
    module_title: str
    concepts: List[str]
    created_at: str

class WebhookAnalyzeRequest(BaseModel):
    session_id: str
    user_id: str

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 3
    threshold: Optional[float] = 0.3

class ChunkResult(BaseModel):
    id: str
    document_id: str
    document_name: str
    chunk_text: str
    similarity: float

class SearchResponse(BaseModel):
    results: List[ChunkResult]

class DocumentIngestionResponse(BaseModel):
    document_id: str
    document_name: str
    chunk_count: int





