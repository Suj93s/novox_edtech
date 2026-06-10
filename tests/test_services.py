import pytest
from services.rag_service import chunk_text
from services.model_router import classify_via_heuristics, route_model

def test_rag_text_chunking():
    """Test the text chunking algorithm in RAG service."""
    text = "A" * 1500
    # chunk_size=1000, chunk_overlap=200
    chunks = chunk_text(text, chunk_size=1000, chunk_overlap=200)
    assert len(chunks) == 2
    assert chunks[0] == "A" * 1000
    # Second chunk should contain the remaining characters plus overlap if necessary
    assert len(chunks[1]) == 700  # character 800 to 1500

def test_rag_text_chunking_overlap_adjustment():
    """Test chunk overlap handling when it is too large."""
    text = "hello world"
    # Overlap >= size -> overlap gets adjusted to size // 5
    chunks = chunk_text(text, chunk_size=5, chunk_overlap=6)
    assert len(chunks) > 0

def test_heuristics_coding_question():
    """Test coding question heuristic trigger."""
    message = "How do I implement a binary search algorithm in python?"
    category = classify_via_heuristics(message)
    assert category == "coding_question"

def test_heuristics_debugging_question():
    """Test debugging question heuristic trigger."""
    message = "My code crashes with: ```IndexError: list index out of range```"
    category = classify_via_heuristics(message)
    assert category == "debugging_question"

def test_heuristics_document_heavy_question():
    """Test document heavy heuristic trigger."""
    message = "Explain this topic."
    retrieved_chunks = [{"chunk_text": "X" * 1600}]
    category = classify_via_heuristics(message, retrieved_chunks)
    assert category == "document_heavy_question"

def test_heuristics_ambiguous_question():
    """Test that ambiguous messages don't match simple heuristics."""
    message = "Hi mentor!"
    category = classify_via_heuristics(message)
    assert category is None

@pytest.mark.asyncio
async def test_route_model_manual_override(mock_openrouter_client):
    """Test model routing with manual override."""
    model, category = await route_model("Hi", request_override="google/gemini-2.5-pro")
    assert model == "google/gemini-2.5-pro"
    assert category == "manual_override"

@pytest.mark.asyncio
async def test_route_model_llm_fallback(mock_openrouter_client):
    """Test route model fallback to LLM classification when heuristics return None."""
    # Set the mock OpenRouter return value to be "debugging_question"
    mock_choice = mock_openrouter_client.chat.completions.create.return_value.choices[0]
    mock_choice.message.content = "debugging_question"
    
    model, category = await route_model("Hi mentor! My app crashed.")
    assert category == "debugging_question"
    assert model == "google/gemini-2.5-pro"
