#!/usr/bin/env python3
"""
Validate Load Testing Setup

Checks that all prerequisites are met for running load tests.
"""

import sys
import subprocess
from pathlib import Path


def check_locust_installed():
    """Check if Locust is installed"""
    try:
        result = subprocess.run(
            ["locust", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Locust is installed: {version}")
            return True
        else:
            print("❌ Locust is not working properly")
            return False
    except FileNotFoundError:
        print("❌ Locust is not installed")
        print("   Install with: pip install locust")
        return False
    except Exception as e:
        print(f"❌ Error checking Locust: {e}")
        return False


def check_server_running():
    """Check if API server is running"""
    try:
        import requests
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            return True
        else:
            print(f"⚠️ API server returned status code: {response.status_code}")
            return False
    except ImportError:
        print("⚠️ requests library not installed (optional check)")
        return True  # Don't fail if requests is not installed
    except Exception as e:
        print(f"❌ API server is not running at http://localhost:8000")
        print("   Start with: python api_server.py")
        return False


def check_files_exist():
    """Check if all required files exist"""
    required_files = [
        "tests/load/locustfile.py",
        "tests/load/config.py",
        "tests/load/analyze_results.py",
        "tests/load/setup_test_users.py",
        "tests/load/README.md",
        "tests/load/LOAD_TESTING_GUIDE.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} not found")
            all_exist = False
    
    return all_exist


def check_reports_directory():
    """Check if reports directory exists"""
    reports_dir = Path("tests/load/reports")
    if reports_dir.exists():
        print(f"✅ Reports directory exists: {reports_dir}")
        return True
    else:
        print(f"⚠️ Reports directory does not exist: {reports_dir}")
        print("   Creating directory...")
        try:
            reports_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created reports directory")
            return True
        except Exception as e:
            print(f"❌ Failed to create reports directory: {e}")
            return False


def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        "locust",
        "fastapi",
        "uvicorn",
        "psycopg2"
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is not installed")
            all_installed = False
    
    return all_installed


def main():
    """Main validation function"""
    print("=" * 70)
    print("Load Testing Setup Validation")
    print("=" * 70)
    print()
    
    checks = [
        ("Locust Installation", check_locust_installed),
        ("Required Files", check_files_exist),
        ("Reports Directory", check_reports_directory),
        ("Python Dependencies", check_dependencies),
        ("API Server", check_server_running),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        print("-" * 70)
        result = check_func()
        results.append((name, result))
        print()
    
    # Summary
    print("=" * 70)
    print("Validation Summary")
    print("=" * 70)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    print()
    
    if all_passed:
        print("✅ All checks passed! You're ready to run load tests.")
        print()
        print("Quick start:")
        print("  1. Ensure API server is running: python api_server.py")
        print("  2. Create test users: python tests/load/setup_test_users.py")
        print("  3. Run load test:")
        print("     - Linux/Mac: ./tests/load/run_load_test.sh normal web")
        print("     - Windows: tests\\load\\run_load_test.bat normal web")
        print()
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
