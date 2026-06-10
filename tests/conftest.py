import pytest
from unittest.mock import MagicMock, AsyncMock
import sys
import os
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import FastAPI app and auth dependency
from api.index import app
from api.auth import get_current_user_id

# Mock database responses data structure
class MockSupabaseQuery:
    def __init__(self, data=None):
        self.data = data or []

    def select(self, *args, **kwargs): return self
    
    def insert(self, data, *args, **kwargs):
        if not self.data:
            if isinstance(data, list):
                self.data = data
            else:
                mock_record = data.copy()
                if "id" not in mock_record:
                    mock_record["id"] = "mock-uuid-123"
                self.data = [mock_record]
        return self

    def update(self, data, *args, **kwargs):
        if self.data:
            for item in self.data:
                item.update(data)
        else:
            self.data = [data]
        return self

    def delete(self, *args, **kwargs): return self
    def eq(self, *args, **kwargs): return self
    def order(self, *args, **kwargs): return self
    def execute(self):
        res = MagicMock()
        res.data = self.data
        return res

class MockSupabaseClient:
    def __init__(self):
        self.mock_data = {}

    def table(self, table_name):
        return MockSupabaseQuery(self.mock_data.get(table_name, []))

    def rpc(self, name, params=None):
        return MockSupabaseQuery(self.mock_data.get(f"rpc_{name}", []))

@pytest.fixture
def mock_supabase_client(monkeypatch):
    client = MockSupabaseClient()
    # Mock in database.supabase
    monkeypatch.setattr("database.supabase.get_supabase_client", lambda: client)
    # Mock in services.rag_service
    monkeypatch.setattr("services.rag_service.get_supabase_client", lambda: client)
    # Mock in api.auth
    monkeypatch.setattr("api.auth.get_supabase_client", lambda: client)
    return client

@pytest.fixture
def mock_openrouter_client(monkeypatch):
    mock_client = MagicMock()
    
    # Mock completion return
    mock_choice = MagicMock()
    mock_choice.message.content = "This is a mock response from Mentor AI."
    mock_completion_res = MagicMock()
    mock_completion_res.choices = [mock_choice]
    
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion_res)

    # Mock embeddings return
    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.1] * 1536
    mock_embedding_res = MagicMock()
    mock_embedding_res.data = [mock_embedding]
    
    mock_client.embeddings = MagicMock()
    mock_client.embeddings.create = AsyncMock(return_value=mock_embedding_res)

    # Mock in services.openrouter
    monkeypatch.setattr("services.openrouter.get_openrouter_client", lambda: mock_client)
    # Mock in agents.mentor_agent
    monkeypatch.setattr("agents.mentor_agent.get_openrouter_client", lambda: mock_client)
    # Mock in services.rag_service
    monkeypatch.setattr("services.rag_service.get_openrouter_client", lambda: mock_client)
    # Mock in services.model_router
    monkeypatch.setattr("services.model_router.get_openrouter_client", lambda: mock_client)
    # Mock in services.profile_analysis
    monkeypatch.setattr("services.profile_analysis.get_openrouter_client", lambda: mock_client)
    
    return mock_client

@pytest.fixture
def test_user_id():
    return "00000000-0000-0000-0000-000000000000"

@pytest.fixture
def client(test_user_id):
    # Override JWT dependency to return our fixed test user ID without JWT verification
    app.dependency_overrides[get_current_user_id] = lambda: test_user_id
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
