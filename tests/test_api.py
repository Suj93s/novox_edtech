import pytest
from unittest.mock import patch, MagicMock

def test_health_check(client):
    """Test health check route."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}

def test_webhook_analyze_success(client, test_user_id, mock_supabase_client):
    """Test background task analyze trigger via webhook."""
    payload = {
        "session_id": "session-123",
        "user_id": test_user_id
    }
    # Mock database to return a session and user profile
    mock_supabase_client.mock_data = {
        "chat_sessions": [{"id": "session-123", "user_id": test_user_id}],
        "chat_messages": [{"id": "msg-123", "session_id": "session-123", "role": "user", "content": "Hi"}],
        "student_profiles": [{"id": "profile-123", "user_id": test_user_id, "behavioral_chart": {"explicit_directives": [], "inferred_traits": []}}]
    }
    
    # We patch run_post_chat_analysis_task so it does not make real network calls
    with patch("api.webhook.run_post_chat_analysis_task") as mock_analysis:
        response = client.post("/api/webhook/analyze", json=payload)
        assert response.status_code == 202
        assert response.json() == {"status": "Accepted", "message": "Background analysis task queued."}

def test_webhook_analyze_forbidden(client, test_user_id):
    """Test webhook fails with 403 when user_id does not match JWT."""
    payload = {
        "session_id": "session-123",
        "user_id": "different-user-id"
    }
    response = client.post("/api/webhook/analyze", json=payload)
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

def test_documents_search(client, test_user_id, mock_supabase_client, mock_openrouter_client):
    """Test document vector search endpoint."""
    mock_supabase_client.mock_data = {
        "rpc_match_document_chunks": [
            {
                "id": "chunk-123",
                "document_id": "doc-123",
                "document_name": "recursion.pdf",
                "chunk_text": "Recursion calls itself.",
                "similarity": 0.85
            }
        ]
    }
    
    payload = {
        "query": "What is recursion?",
        "limit": 2,
        "threshold": 0.2
    }
    
    response = client.post("/api/documents/search", json=payload)
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["document_name"] == "recursion.pdf"
    assert results[0]["similarity"] == 0.85

def test_chat_endpoint_new_session(client, test_user_id, mock_supabase_client, mock_openrouter_client):
    """Test `/api/chat` when no session_id is provided, checking auto-creation."""
    mock_supabase_client.mock_data = {
        "chat_sessions": [{"id": "new-session-123", "user_id": test_user_id}],
        "student_profiles": [{"id": "profile-123", "user_id": test_user_id, "behavioral_chart": {"explicit_directives": [], "inferred_traits": []}}],
        "chat_messages": []
    }
    
    payload = {
        "message": "Hello mentor!",
        "course_name": "Advanced Java",
        "module_title": "Recursion and Memory"
    }
    
    # Mock routing decision & curriculum fetch
    with patch("api.chat.route_model", return_value=("google/gemini-2.5-flash-lite", "simple_question")), \
         patch("api.chat.get_module", return_value={"id": "module-123", "course_name": "Advanced Java", "module_title": "Recursion and Memory", "concepts": []}), \
         patch("api.chat.get_or_create_mastery", return_value={"proficiency_score": 0.25}), \
         patch("api.chat.queue_analysis_task") as mock_queue_analysis:
         
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"] == "This is a mock response from Mentor AI."
        assert data["session_id"] == "new-session-123"
        mock_queue_analysis.assert_called_once()
