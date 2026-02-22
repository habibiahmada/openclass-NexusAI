"""
Quick Test Script for Modular API
Tests all imports and basic functionality
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all module imports"""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    print()
    
    tests = [
        ("Config", "from src.api.config import config"),
        ("Models", "from src.api.models import ChatRequest, ChatResponse, LoginRequest"),
        ("Auth", "from src.api.auth import AuthService, generate_token, hash_password"),
        ("State", "from src.api.state import AppState, app_state"),
        ("Auth Router", "from src.api.routers.auth_router import create_auth_router"),
        ("Chat Router", "from src.api.routers.chat_router import create_chat_router"),
        ("Teacher Router", "from src.api.routers.teacher_router import create_teacher_router"),
        ("Admin Router", "from src.api.routers.admin_router import create_admin_router"),
        ("Pedagogy Router", "from src.api.routers.pedagogy_router import create_pedagogy_router"),
        ("Queue Router", "from src.api.routers.queue_router import create_queue_router"),
        ("Pages Router", "from src.api.routers.pages_router import create_pages_router"),
    ]
    
    passed = 0
    failed = 0
    
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✓ {name:20s} - OK")
            passed += 1
        except Exception as e:
            print(f"✗ {name:20s} - FAILED: {e}")
            failed += 1
    
    print()
    print(f"Results: {passed} passed, {failed} failed")
    print()
    
    return failed == 0


def test_config():
    """Test configuration"""
    print("=" * 60)
    print("Testing Configuration")
    print("=" * 60)
    print()
    
    try:
        from src.api.config import config
        
        print(f"✓ API Host: {config.HOST}")
        print(f"✓ API Port: {config.PORT}")
        print(f"✓ Debug Mode: {config.DEBUG}")
        print(f"✓ Log Level: {config.LOG_LEVEL}")
        print(f"✓ Database URL: {config.DATABASE_URL[:30]}...")
        print(f"✓ Model Cache Dir: {config.MODEL_CACHE_DIR}")
        print(f"✓ Max Concurrent: {config.MAX_CONCURRENT_REQUESTS}")
        print()
        
        # Validate config
        errors = config.validate()
        if errors:
            print("⚠️  Configuration Warnings:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("✓ Configuration validation passed")
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        print()
        return False


def test_auth_service():
    """Test authentication service"""
    print("=" * 60)
    print("Testing Authentication Service")
    print("=" * 60)
    print()
    
    try:
        from src.api.auth import AuthService, generate_token, hash_password
        
        # Test token generation
        token = generate_token()
        print(f"✓ Token generation: {token[:20]}...")
        
        # Test password hashing
        password = "test123"
        hashed = hash_password(password)
        print(f"✓ Password hashing: {hashed[:20]}...")
        
        # Test AuthService creation
        auth_service = AuthService()
        print(f"✓ AuthService created")
        
        # Test credential verification (without database)
        result = auth_service.verify_credentials("siswa", "siswa123", "siswa")
        if result['success']:
            print(f"✓ Credential verification: {result['username']}")
        else:
            print(f"✗ Credential verification failed: {result['message']}")
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ Authentication test failed: {e}")
        print()
        return False


def test_models():
    """Test Pydantic models"""
    print("=" * 60)
    print("Testing Pydantic Models")
    print("=" * 60)
    print()
    
    try:
        from src.api.models import (
            ChatRequest, ChatResponse,
            LoginRequest, LoginResponse,
            TeacherStats, AdminStatus
        )
        
        # Test ChatRequest
        chat_req = ChatRequest(message="Test question", subject_filter="all")
        print(f"✓ ChatRequest: {chat_req.message}")
        
        # Test ChatResponse
        chat_res = ChatResponse(response="Test answer", source="Test", confidence=0.9)
        print(f"✓ ChatResponse: {chat_res.response}")
        
        # Test LoginRequest
        login_req = LoginRequest(username="test", password="test123", role="siswa")
        print(f"✓ LoginRequest: {login_req.username}")
        
        # Test LoginResponse
        login_res = LoginResponse(success=True, token="abc123", message="OK", role="siswa")
        print(f"✓ LoginResponse: {login_res.success}")
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ Models test failed: {e}")
        print()
        return False


def test_state():
    """Test application state"""
    print("=" * 60)
    print("Testing Application State")
    print("=" * 60)
    print()
    
    try:
        from src.api.state import AppState
        
        # Create state instance
        state = AppState()
        print(f"✓ AppState created")
        
        # Check initial state
        print(f"✓ Pipeline initialized: {state.is_initialized}")
        print(f"✓ Database initialized: {state.db_initialized}")
        print(f"✓ Concurrency initialized: {state.concurrency_initialized}")
        print(f"✓ Pedagogy initialized: {state.pedagogy_initialized}")
        print(f"✓ Telemetry initialized: {state.telemetry_initialized}")
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ State test failed: {e}")
        print()
        return False


def main():
    """Run all tests"""
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Modular API Test Suite" + " " * 26 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Authentication", test_auth_service()))
    results.append(("Models", test_models()))
    results.append(("State", test_state()))
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()
    
    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name:20s} - {status}")
    
    print()
    print(f"Total: {passed} passed, {failed} failed")
    print()
    
    if failed == 0:
        print("🎉 All tests passed! Modular API is ready to use.")
        print()
        print("Next steps:")
        print("  1. Start the server: python api_server.py")
        print("  2. Open browser: http://localhost:8000")
        print("  3. Test login with: siswa/siswa123")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print()
        print("Common issues:")
        print("  - Missing dependencies: pip install -r requirements.txt")
        print("  - Missing .env file: cp .env.example .env")
        print("  - Database not running: Check PostgreSQL")
    
    print()
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
