"""
Verification script for Task 2.7: Replace in-memory storage with database operations

This script verifies that:
1. In-memory storage (active_tokens dict, state.chat_logs list) has been removed
2. Database repositories are imported and initialized
3. API endpoints use repositories instead of in-memory storage
"""

import ast
import sys
from pathlib import Path


def check_api_server_changes():
    """Verify changes in api_server.py"""
    api_server_path = Path("api_server.py")
    
    if not api_server_path.exists():
        print("❌ api_server.py not found")
        return False
    
    content = api_server_path.read_text(encoding='utf-8')
    
    checks = {
        "Database imports present": any([
            "from src.persistence.database_manager import DatabaseManager" in content,
            "from src.persistence.session_repository import SessionRepository" in content,
            "from src.persistence.chat_history_repository import ChatHistoryRepository" in content,
        ]),
        "In-memory active_tokens removed": 'active_tokens = {}' not in content or '# active_tokens = {}' in content,
        "In-memory chat_logs removed": 'self.chat_logs = []' not in content or '# self.chat_logs = []' in content,
        "SessionRepository used": "session_repo" in content,
        "ChatHistoryRepository used": "chat_history_repo" in content,
        "Database initialization present": "initialize_database" in content,
        "Environment variable loading": "load_dotenv()" in content,
        "DATABASE_URL used": "DATABASE_URL" in content,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def check_env_files():
    """Verify .env files have database configuration"""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    checks = {}
    
    if env_path.exists():
        env_content = env_path.read_text(encoding='utf-8')
        checks[".env has DATABASE_URL"] = "DATABASE_URL" in env_content
    else:
        checks[".env exists"] = False
    
    if env_example_path.exists():
        env_example_content = env_example_path.read_text(encoding='utf-8')
        checks[".env.example has DATABASE_URL"] = "DATABASE_URL" in env_example_content
    else:
        checks[".env.example exists"] = False
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def check_specific_endpoints():
    """Verify specific endpoint changes"""
    api_server_path = Path("api_server.py")
    content = api_server_path.read_text(encoding='utf-8')
    
    checks = {
        "Login uses SessionRepository.create_session": "session_repo.create_session" in content,
        "Logout uses SessionRepository.delete_user_sessions": "session_repo.delete_user_sessions" in content,
        "Chat saves to ChatHistoryRepository": "chat_history_repo.save_chat" in content,
        "Teacher stats uses ChatHistoryRepository": "chat_history_repo.get_recent_chats" in content,
        "verify_token uses SessionRepository": "session_repo.get_session_by_token" in content,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def main():
    print("=" * 70)
    print("Task 2.7 Verification: Replace in-memory storage with database operations")
    print("=" * 70)
    print()
    
    print("Checking api_server.py changes...")
    print("-" * 70)
    api_server_ok = check_api_server_changes()
    print()
    
    print("Checking environment configuration...")
    print("-" * 70)
    env_ok = check_env_files()
    print()
    
    print("Checking specific endpoint implementations...")
    print("-" * 70)
    endpoints_ok = check_specific_endpoints()
    print()
    
    print("=" * 70)
    if api_server_ok and env_ok and endpoints_ok:
        print("✅ All checks passed! Task 2.7 implementation verified.")
        print()
        print("Next steps:")
        print("1. Setup PostgreSQL database (see database/setup_database.md)")
        print("2. Run the schema: psql -U nexusai -d nexusai_db -f database/schema.sql")
        print("3. Start the API server: python api_server.py")
        print("4. Test login and verify sessions are stored in database")
        return 0
    else:
        print("❌ Some checks failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
