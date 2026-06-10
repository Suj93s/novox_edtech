import pytest
from unittest.mock import MagicMock
from agents.mentor_agent import process_chat_message

@pytest.mark.asyncio
async def test_guardrail_default_socratic(mock_openrouter_client):
    """Test that default Socratic instruction is injected for standard queries."""
    history = [{"role": "user", "content": "I am struggling with recursion."}]
    
    await process_chat_message(messages_history=history)
    
    # Retrieve call arguments
    called_messages = mock_openrouter_client.chat.completions.create.call_args[1]["messages"]
    system_prompt = called_messages[0]["content"]
    
    assert "ACTIVE SOCRATIC TUTORING" in system_prompt
    assert "Step 1: Validate Effort" in system_prompt
    assert "Step 2: Conceptual Hint" in system_prompt
    assert "Step 3: Leading Question" in system_prompt

@pytest.mark.asyncio
async def test_guardrail_refusal_trigger(mock_openrouter_client):
    """Test that strict refusal directive is injected when requesting code."""
    history = [{"role": "user", "content": "Can you write the code for quicksort for me?"}]
    
    await process_chat_message(messages_history=history)
    
    called_messages = mock_openrouter_client.chat.completions.create.call_args[1]["messages"]
    system_prompt = called_messages[0]["content"]
    
    assert "DIRECT ANSWER REQUEST DETECTED" in system_prompt
    assert "You MUST refuse politely but firmly" in system_prompt
    assert "Do not dump the code!" in system_prompt

@pytest.mark.asyncio
async def test_guardrail_exception_trigger(mock_openrouter_client):
    """Test that exception directive is injected for theoretical/definition queries."""
    history = [{"role": "user", "content": "What is stack memory in Java?"}]
    
    await process_chat_message(messages_history=history)
    
    called_messages = mock_openrouter_client.chat.completions.create.call_args[1]["messages"]
    system_prompt = called_messages[0]["content"]
    
    assert "EXCEPTION CASE ACTIVE" in system_prompt
    assert "You are ALLOWED to provide a direct answer" in system_prompt

@pytest.mark.asyncio
async def test_guardrail_disabled_via_profile(mock_openrouter_client):
    """Test that guardrails can be disabled via student profile system_metadata override."""
    history = [{"role": "user", "content": "Write the code for me."}]
    student_profile = {
        "user_id": "user-123",
        "system_metadata": {
            "guardrails_enabled": False
        }
    }
    
    await process_chat_message(messages_history=history, student_profile=student_profile)
    
    called_messages = mock_openrouter_client.chat.completions.create.call_args[1]["messages"]
    system_prompt = called_messages[0]["content"]
    
    # Guardrails disabled, so no guardrail directive should be appended to the prompt
    assert "DIRECT ANSWER REQUEST DETECTED" not in system_prompt
    assert "ACTIVE SOCRATIC TUTORING" not in system_prompt

@pytest.mark.asyncio
async def test_guardrail_strictness_override(mock_openrouter_client):
    """Test that socratic strictness can be set to moderate via profile metadata."""
    history = [{"role": "user", "content": "Write the code."}]
    student_profile = {
        "user_id": "user-123",
        "system_metadata": {
            "socratic_strictness": "moderate"
        }
    }
    
    await process_chat_message(messages_history=history, student_profile=student_profile)
    
    called_messages = mock_openrouter_client.chat.completions.create.call_args[1]["messages"]
    system_prompt = called_messages[0]["content"]
    
    assert "SOLUTION REQUEST DETECTED" in system_prompt
    assert "Avoid giving the direct solution" in system_prompt
    assert "DIRECT ANSWER REQUEST DETECTED" not in system_prompt
