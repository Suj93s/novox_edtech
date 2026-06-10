import os
import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set environment variables before importing anything that uses them
os.environ["ENVIRONMENT"] = "development"

# Set up simple console logging format
import logging
logging.basicConfig(
    level=logging.WARNING, # Suppress noisy verbose logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Color constants for rich terminal formatting
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Utility to mock clients for Mock Mode
def setup_mock_environment():
    print(f"\n{Colors.WARNING}Setting up Mock Environment (Bypassing real database and LLM)...{Colors.ENDC}")
    
    # Mock database responses
    class MockSupabaseQuery:
        def __init__(self, data=None):
            self.data = data or []
        def select(self, *args, **kwargs): return self
        def insert(self, *args, **kwargs): return self
        def update(self, *args, **kwargs): return self
        def delete(self, *args, **kwargs): return self
        def eq(self, *args, **kwargs): return self
        def order(self, *args, **kwargs): return self
        def execute(self):
            res = MagicMock()
            res.data = self.data
            return res

    class MockSupabaseClient:
        def table(self, table_name):
            # Prepopulate mock responses
            if table_name == "chat_sessions":
                return MockSupabaseQuery([{"id": "mock-session-1111", "user_id": "mock-user-uuid"}])
            elif table_name == "student_profiles":
                return MockSupabaseQuery([{
                    "id": "mock-profile-2222",
                    "user_id": "mock-user-uuid",
                    "behavioral_chart": {
                        "explicit_directives": ["Explain using step-by-step logic", "Avoid giving answers directly"],
                        "inferred_traits": ["Prefers visual analogies"]
                    }
                }])
            elif table_name == "novox_curriculum":
                return MockSupabaseQuery([{
                    "id": "mock-module-3333",
                    "course_name": "Advanced Java",
                    "module_title": "Recursion and Memory",
                    "concepts": ["recursive functions", "call stack", "base case"]
                }])
            elif table_name == "student_mastery":
                return MockSupabaseQuery([{
                    "id": "mock-mastery-4444",
                    "user_id": "mock-user-uuid",
                    "module_id": "mock-module-3333",
                    "proficiency_score": 0.45
                }])
            elif table_name == "chat_messages":
                return MockSupabaseQuery([])
            return MockSupabaseQuery([])
            
        def rpc(self, name, params=None):
            return MockSupabaseQuery([])

    mock_db = MockSupabaseClient()
    import database.supabase
    database.supabase.get_supabase_client = lambda: mock_db

    # Mock OpenRouter Client
    mock_or = MagicMock()
    
    mock_choice = MagicMock()
    mock_choice.message.content = "Mock response: Recursion is a method of solving problems where the solution depends on solutions to smaller instances of the same problem."
    mock_completion_res = MagicMock()
    mock_completion_res.choices = [mock_choice]
    
    async def mock_create_completion(*args, **kwargs):
        return mock_completion_res
        
    mock_or.chat = MagicMock()
    mock_or.chat.completions = MagicMock()
    mock_or.chat.completions.create = AsyncMock(side_effect=mock_create_completion)

    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.0] * 1536
    mock_embedding_res = MagicMock()
    mock_embedding_res.data = [mock_embedding]
    
    async def mock_create_embedding(*args, **kwargs):
        return mock_embedding_res
        
    mock_or.embeddings = MagicMock()
    mock_or.embeddings.create = AsyncMock(side_effect=mock_create_embedding)

    import services.openrouter
    services.openrouter.get_openrouter_client = lambda: mock_or

async def main():
    print(f"{Colors.HEADER}{Colors.BOLD}=================================================={Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}          NOVOX MENTOR AI PLAYGROUND              {Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}=================================================={Colors.ENDC}")
    
    print("Select run mode:")
    print("  1. Mock Mode (Local testing, no credentials required)")
    print("  2. Live Mode (Connects to Supabase and OpenRouter using .env)")
    
    choice = input("Enter choice (1 or 2, default: 1): ").strip()
    if choice == "2":
        # Check if environment is configured
        from core.config import settings
        if not settings.SUPABASE_URL or not settings.OPENROUTER_API_KEY:
            print(f"{Colors.FAIL}Error: Supabase URL or OpenRouter API key is missing in .env!{Colors.ENDC}")
            print("Falling back to Mock Mode...")
            setup_mock_environment()
        else:
            print(f"\n{Colors.GREEN}Connected to Live Services:{Colors.ENDC}")
            print(f" - Supabase: {settings.SUPABASE_URL}")
            print(f" - Model Router Category models configured.")
    else:
        setup_mock_environment()

    # Import services only after mock environment might be set up
    from services.profile_service import get_or_create_profile
    from services.chat_service import create_chat_session, get_session_messages, save_message
    from services.curriculum_service import get_module
    from services.mastery_service import get_or_create_mastery
    from services.rag_service import search_relevant_chunks
    from services.model_router import route_model
    from agents.mentor_agent import process_chat_message

    # Configuration params
    user_id = "00000000-0000-0000-0000-000000000000"
    course_name = "Advanced Java"
    module_title = "Recursion and Memory"

    print(f"\n{Colors.BOLD}--- Target Session Parameters ---{Colors.ENDC}")
    print(f"User ID:    {Colors.CYAN}{user_id}{Colors.ENDC}")
    print(f"Course:     {Colors.CYAN}{course_name}{Colors.ENDC}")
    print(f"Module:     {Colors.CYAN}{module_title}{Colors.ENDC}")
    print("---------------------------------\n")

    # Initialize session state
    try:
        profile = get_or_create_profile(user_id)
        session = create_chat_session(user_id)
        session_id = session
        
        module = get_module(course_name, module_title)
        mastery = None
        if module:
            mastery = get_or_create_mastery(user_id, module["id"])
            
        print(f"{Colors.GREEN}Chat Session Initialized successfully!{Colors.ENDC}")
        print(f"Session ID: {Colors.CYAN}{session_id}{Colors.ENDC}")
        if profile:
            directives = profile.get("behavioral_chart", {}).get("explicit_directives", [])
            print(f"Injected student profile directives: {Colors.BLUE}{directives}{Colors.ENDC}")
        if mastery:
            print(f"Current Student Proficiency Score: {Colors.BLUE}{mastery.get('proficiency_score', 0.0)}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}Initialization failed: {e}{Colors.ENDC}")
        print("Please check your .env database connection and schema.sql deployment.")
        return

    print(f"\n{Colors.BOLD}Chat started. Type 'exit' or 'quit' to end the session.{Colors.ENDC}\n")

    while True:
        try:
            user_msg = input(f"{Colors.BOLD}Student:{Colors.ENDC} ")
            if user_msg.strip().lower() in ["exit", "quit"]:
                print(f"\n{Colors.HEADER}Thank you for learning with Novox Mentor AI!{Colors.ENDC}")
                break
                
            if not user_msg.strip():
                continue
                
            print(f"\n{Colors.BLUE}[Processing message...]{Colors.ENDC}")
            
            # 1. Save user message
            save_message(session_id, "user", user_msg)
            
            # 2. Get history
            history = get_session_messages(session_id)
            
            # 3. Retrieve document chunks
            chunks = await search_relevant_chunks(user_msg, user_id)
            if chunks:
                print(f" {Colors.CYAN}* RAG Search retrieved {len(chunks)} relevant document passages.{Colors.ENDC}")
                
            # 4. Route model
            selected_model, category = await route_model(user_msg, history, chunks)
            print(f" {Colors.CYAN}* Intelligent Router matched query category: '{category}' -> using model: '{selected_model}'{Colors.ENDC}")
            
            # 5. Generate AI response
            ai_response = await process_chat_message(
                messages_history=history,
                student_profile=profile,
                curriculum_context=module,
                student_mastery=mastery,
                retrieved_chunks=chunks,
                model_name=selected_model
            )
            
            # 6. Save AI response
            save_message(session_id, "assistant", ai_response)
            
            print(f"\n{Colors.GREEN}{Colors.BOLD}Mentor AI:{Colors.ENDC} {ai_response}\n")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print(f"\n{Colors.HEADER}Session interrupted.{Colors.ENDC}")
            break
        except Exception as e:
            print(f"\n{Colors.FAIL}Error: {e}{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        # Run async event loop
        asyncio.run(main())
    except Exception as e:
        print(f"Unhandled script exception: {e}")
