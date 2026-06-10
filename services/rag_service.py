import io
import uuid
import logging
import asyncio
from pypdf import PdfReader
from database.supabase import get_supabase_client
from services.openrouter import get_openrouter_client

logger = logging.getLogger(__name__)

async def generate_embedding(text: str) -> list[float]:
    """
    Generates a 1536-dimensional embedding vector using the
    openai/text-embedding-3-small model via the OpenRouter API.
    """
    if not text.strip():
        raise ValueError("Cannot generate embedding for empty text.")
        
    client = get_openrouter_client()
    try:
        logger.info("Requesting embedding from OpenRouter...")
        response = await client.embeddings.create(
            model="openai/text-embedding-3-small",
            input=text
        )
        embedding = response.data[0].embedding
        if len(embedding) != 1536:
            raise ValueError(f"Expected 1536 dimensions, got {len(embedding)}")
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding via OpenRouter: {e}", exc_info=True)
        raise RuntimeError(f"Failed to generate embedding: {e}")

def extract_text_from_pdf(content: bytes) -> str:
    """
    Extracts raw text from PDF bytes using pypdf.
    """
    try:
        reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error parsing PDF file: {e}", exc_info=True)
        raise ValueError(f"Failed to parse PDF document: {e}")

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """
    Splits text into chunks of character length chunk_size with chunk_overlap.
    """
    if not text:
        return []
    chunks = []
    start = 0
    text_len = len(text)
    
    # Safeguard against infinite loops
    if chunk_overlap >= chunk_size:
        chunk_overlap = chunk_size // 5
        
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start += (chunk_size - chunk_overlap)
        
    return chunks

async def ingest_document(filename: str, content: bytes, user_id: str) -> dict:
    """
    Ingests a PDF, TXT, or Markdown document, chunks it,
    generates OpenRouter embeddings, and inserts them into Supabase.
    """
    logger.info(f"Starting ingestion of document '{filename}' for user '{user_id}'")
    
    # 1. Parse and extract text
    ext = filename.split(".")[-1].lower()
    if ext == "pdf":
        text = extract_text_from_pdf(content)
    elif ext in ["txt", "md", "markdown"]:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback to ISO-8859-1
            text = content.decode("iso-8859-1")
    else:
        raise ValueError(f"Unsupported file format: .{ext}. Only PDF, TXT, and Markdown files are supported.")
        
    if not text.strip():
        raise ValueError("The uploaded document does not contain any readable text.")
        
    # 2. Chunk text
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("Could not extract any meaningful chunks from the document.")
    logger.info(f"Document '{filename}' split into {len(chunks)} chunks.")
    
    # 3. Generate document UUID
    document_id = str(uuid.uuid4())
    
    # 4. Generate embeddings concurrently using a semaphore to limit rate limits
    sem = asyncio.Semaphore(5)
    
    async def get_embedding_with_sem(chunk: str):
        async with sem:
            return await generate_embedding(chunk)
            
    try:
        tasks = [get_embedding_with_sem(chunk) for chunk in chunks]
        embeddings = await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Error generating embeddings for document '{filename}': {e}", exc_info=True)
        raise RuntimeError(f"Embedding generation failed: {e}")
        
    # 5. Insert document chunks into Supabase
    client = get_supabase_client()
    chunks_to_insert = []
    for chunk, embedding in zip(chunks, embeddings):
        chunks_to_insert.append({
            "user_id": user_id,
            "document_id": document_id,
            "document_name": filename,
            "chunk_text": chunk,
            "embedding": embedding
        })
        
    try:
        logger.info(f"Inserting {len(chunks_to_insert)} chunks for document '{filename}' into table 'document_chunks'.")
        response = client.table("document_chunks").insert(chunks_to_insert).execute()
        if not response.data:
            raise RuntimeError("Database insertion yielded no results.")
            
        logger.info(f"Successfully inserted all chunks for document '{filename}'. Document ID is: {document_id}")
        return {
            "document_id": document_id,
            "document_name": filename,
            "chunk_count": len(chunks_to_insert)
        }
    except Exception as e:
        logger.error(f"Database error while saving document '{filename}': {e}", exc_info=True)
        raise RuntimeError(f"Failed to store document in database: {e}")

async def search_relevant_chunks(
    query: str,
    user_id: str,
    threshold: float = 0.3,
    limit: int = 3
) -> list[dict]:
    """
    Searches the database for chunks similar to the query, filtering by user_id.
    """
    logger.info(f"Searching document chunks for user '{user_id}' with query: '{query}'")
    if not query.strip():
        return []
        
    try:
        # 1. Generate query embedding
        query_embedding = await generate_embedding(query)
        
        # 2. Execute pgvector similarity matching via Supabase RPC
        client = get_supabase_client()
        params = {
            "query_embedding": query_embedding,
            "match_threshold": threshold,
            "match_count": limit,
            "p_user_id": user_id
        }
        
        response = client.rpc("match_document_chunks", params).execute()
        results = response.data or []
        logger.info(f"Found {len(results)} relevant chunks matching user query.")
        return results
    except Exception as e:
        logger.error(f"Error performing document similarity search: {e}", exc_info=True)
        # Suppress exception and return empty array to keep chat flow functioning
        return []
