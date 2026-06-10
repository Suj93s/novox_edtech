import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from agents.mentor_agent import process_chat_message_stream

class MockStreamChunk:
    def __init__(self, content):
        mock_choice = MagicMock()
        mock_choice.delta.content = content
        self.choices = [mock_choice]

async def mock_async_iterator(chunks):
    for chunk in chunks:
        yield MockStreamChunk(chunk)

@pytest.fixture
def mock_openrouter_stream(mock_openrouter_client):
    """Fixture to configure mock openrouter client to return a stream."""
    async def mock_create(*args, **kwargs):
        if kwargs.get("stream"):
            return mock_async_iterator(["Hello", " Socratic", " world!"])
        # Fallback to default return value
        return mock_openrouter_client.chat.completions.create.return_value
        
    mock_openrouter_client.chat.completions.create = AsyncMock(side_effect=mock_create)
    return mock_openrouter_client

@pytest.mark.asyncio
async def test_process_chat_message_stream(mock_openrouter_stream):
    """Test process_chat_message_stream generator outputs tokens."""
    history = [{"role": "user", "content": "Hello mentor"}]
    
    tokens = []
    async for token in process_chat_message_stream(messages_history=history):
        tokens.append(token)
        
    assert tokens == ["Hello", " Socratic", " world!"]

def test_api_chat_stream_endpoint(client, test_user_id, mock_supabase_client, mock_openrouter_stream):
    """Test `/api/chat/stream` SSE output streaming format and db save execution."""
    mock_supabase_client.mock_data = {
        "chat_sessions": [{"id": "session-1234", "user_id": test_user_id}],
        "student_profiles": [{"id": "profile-1234", "user_id": test_user_id, "behavioral_chart": {"explicit_directives": [], "inferred_traits": []}}],
        "chat_messages": []
    }
    
    payload = {
        "message": "Start streaming",
        "course_name": "Advanced Java",
        "module_title": "Recursion and Memory"
    }
    
    with patch("api.chat.route_model", return_value=("google/gemini-2.5-flash-lite", "simple_question")), \
         patch("api.chat.get_module", return_value={"id": "module-1234", "course_name": "Advanced Java", "module_title": "Recursion and Memory", "concepts": []}), \
         patch("api.chat.get_or_create_mastery", return_value={"proficiency_score": 0.5}), \
         patch("api.chat.queue_analysis_task") as mock_queue_analysis:
         
        response = client.post("/api/chat/stream", json=payload)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        
        # Read SSE output lines
        lines = [(line.decode("utf-8") if isinstance(line, bytes) else line).strip() for line in response.iter_lines() if line]
        
        # Parse data packets
        events = []
        for line in lines:
            if line.startswith("data:"):
                data_str = line[len("data:"):].strip()
                events.append(json.loads(data_str))
                
        # First event should yield the session_id
        assert len(events) >= 4
        assert events[0]["session_id"] == "session-1234"
        
        # Intermediate events should stream the tokens
        assert events[1]["token"] == "Hello"
        assert events[2]["token"] == " Socratic"
        assert events[3]["token"] == " world!"
        
        # Background task queue should be triggered after completion
        mock_queue_analysis.assert_called_once()
