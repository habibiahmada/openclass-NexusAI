"""
System Verification Script

Verifies that all phases 0-6 are properly implemented and integrated:
- Phase 0: Preparation (backup exists)
- Phase 1: Folder structure (edge_runtime, aws_control_plane)
- Phase 2: Database persistence (PostgreSQL tables)
- Phase 3: AWS infrastructure (optional, skip if not configured)
- Phase 4: VKP packaging (classes exist)
- Phase 5: VKP pull mechanism (classes exist)
- Phase 6: Pedagogical engine (integrated with API)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

def check_phase_0():
    """Phase 0: Preparation and Audit"""
    print("\n" + "=" * 60)
    print("PHASE 0: Preparation and Audit")
    print("=" * 60)
    
    # Check if backup exists
    backup_dir = project_root / 'backups' / 'pre-refactoring'
    if backup_dir.exists():
        backups = list(backup_dir.glob('backup_*'))
        if backups:
            print(f"✓ Backup exists: {len(backups)} backup(s) found")
            return True
        else:
            print("✗ No backups found in backups/pre-refactoring/")
            return False
    else:
        print("✗ Backup directory not found")
        return False

def check_phase_1():
    """Phase 1: Folder Structure Alignment"""
    print("\n" + "=" * 60)
    print("PHASE 1: Folder Structure Alignment")
    print("=" * 60)
    
    checks = []
    
    # Check edge_runtime folder
    edge_runtime = project_root / 'src' / 'edge_runtime'
    if edge_runtime.exists():
        print("✓ src/edge_runtime/ exists")
        checks.append(True)
    else:
        print("✗ src/edge_runtime/ not found")
        checks.append(False)
    
    # Check aws_control_plane folder
    aws_control_plane = project_root / 'src' / 'aws_control_plane'
    if aws_control_plane.exists():
        print("✓ src/aws_control_plane/ exists")
        checks.append(True)
    else:
        print("✗ src/aws_control_plane/ not found")
        checks.append(False)
    
    # Check models folder (not models/cache)
    models = project_root / 'models'
    if models.exists():
        print("✓ models/ exists")
        checks.append(True)
    else:
        print("✗ models/ not found")
        checks.append(False)
    
    return all(checks)

def check_phase_2():
    """Phase 2: Database Persistence Layer"""
    print("\n" + "=" * 60)
    print("PHASE 2: Database Persistence Layer")
    print("=" * 60)
    
    checks = []
    
    # Check database components exist
    persistence_dir = project_root / 'src' / 'persistence'
    required_files = [
        'database_manager.py',
        'user_repository.py',
        'session_repository.py',
        'chat_history_repository.py',
        'subject_repository.py',
    ]
    
    for file in required_files:
        file_path = persistence_dir / file
        if file_path.exists():
            print(f"✓ {file} exists")
            checks.append(True)
        else:
            print(f"✗ {file} not found")
            checks.append(False)
    
    # Check database connection
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f"✓ DATABASE_URL is set")
        checks.append(True)
        
        # Try to connect
        try:
            import psycopg2
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            print("✓ Database connection successful")
            checks.append(True)
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            checks.append(False)
    else:
        print("✗ DATABASE_URL not set in .env")
        checks.append(False)
    
    return all(checks)

def check_phase_3():
    """Phase 3: AWS Infrastructure Setup (Optional)"""
    print("\n" + "=" * 60)
    print("PHASE 3: AWS Infrastructure Setup (Optional)")
    print("=" * 60)
    
    # Check if AWS credentials are configured
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    if aws_access_key and aws_secret_key:
        print("✓ AWS credentials configured")
        print("  (Skipping AWS infrastructure verification - requires AWS account)")
        return True
    else:
        print("⊘ AWS credentials not configured (optional)")
        print("  System can run without AWS for local-only mode")
        return True  # Not required for local operation

def check_phase_4():
    """Phase 4: VKP Packaging System"""
    print("\n" + "=" * 60)
    print("PHASE 4: VKP Packaging System")
    print("=" * 60)
    
    checks = []
    
    # Check VKP components exist
    vkp_dir = project_root / 'src' / 'vkp'
    required_files = [
        'packager.py',
        'models.py',
    ]
    
    for file in required_files:
        file_path = vkp_dir / file
        if file_path.exists():
            print(f"✓ {file} exists")
            checks.append(True)
        else:
            print(f"✗ {file} not found")
            checks.append(False)
    
    # Try to import VKPPackager
    try:
        from src.vkp.packager import VKPPackager
        print("✓ VKPPackager can be imported")
        checks.append(True)
    except ImportError as e:
        print(f"✗ Failed to import VKPPackager: {e}")
        checks.append(False)
    
    return all(checks)

def check_phase_5():
    """Phase 5: VKP Pull Mechanism"""
    print("\n" + "=" * 60)
    print("PHASE 5: VKP Pull Mechanism")
    print("=" * 60)
    
    checks = []
    
    # Check VKP puller exists
    puller_file = project_root / 'src' / 'vkp' / 'puller.py'
    if puller_file.exists():
        print("✓ puller.py exists")
        checks.append(True)
    else:
        print("✗ puller.py not found")
        checks.append(False)
    
    # Try to import VKPPuller
    try:
        from src.vkp.puller import VKPPuller
        print("✓ VKPPuller can be imported")
        checks.append(True)
    except ImportError as e:
        print(f"✗ Failed to import VKPPuller: {e}")
        checks.append(False)
    
    return all(checks)

def check_phase_6():
    """Phase 6: Pedagogical Intelligence Engine"""
    print("\n" + "=" * 60)
    print("PHASE 6: Pedagogical Intelligence Engine")
    print("=" * 60)
    
    checks = []
    
    # Check pedagogical components exist
    pedagogy_dir = project_root / 'src' / 'pedagogy'
    required_files = [
        'mastery_tracker.py',
        'weak_area_detector.py',
        'question_generator.py',
        'report_generator.py',
        'integration.py',
    ]
    
    for file in required_files:
        file_path = pedagogy_dir / file
        if file_path.exists():
            print(f"✓ {file} exists")
            checks.append(True)
        else:
            print(f"✗ {file} not found")
            checks.append(False)
    
    # Check integration with state.py (modular architecture)
    state_file = project_root / 'src' / 'api' / 'state.py'
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check if pedagogical integration is initialized
            if 'from src.pedagogy.integration import' in content or 'pedagogical_integration' in content:
                print("✓ Pedagogical integration initialized in state.py")
                checks.append(True)
            else:
                print("✗ Pedagogical integration not initialized in state.py")
                checks.append(False)
    else:
        print("✗ state.py not found")
        checks.append(False)
    
    # Check if pedagogy router exists
    pedagogy_router = project_root / 'src' / 'api' / 'routers' / 'pedagogy_router.py'
    if pedagogy_router.exists():
        with open(pedagogy_router, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check if pedagogical endpoints exist
            if '/api/student/progress' in content or '/progress' in content:
                print("✓ Pedagogical endpoints exist in pedagogy_router.py")
                checks.append(True)
            else:
                print("✗ Pedagogical endpoints not found in pedagogy_router.py")
                checks.append(False)
    else:
        print("✗ pedagogy_router.py not found")
        checks.append(False)
    
    # Check if process_student_question is called in chat router
    chat_router = project_root / 'src' / 'api' / 'routers' / 'chat_router.py'
    if chat_router.exists():
        with open(chat_router, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if 'process_student_question' in content:
                print("✓ process_student_question called in chat_router.py")
                checks.append(True)
            else:
                print("✗ process_student_question not called in chat_router.py")
                checks.append(False)
    else:
        print("✗ chat_router.py not found")
        checks.append(False)
    
    return all(checks)

def run_tests():
    """Run test suite"""
    print("\n" + "=" * 60)
    print("RUNNING TEST SUITE")
    print("=" * 60)
    
    import subprocess
    
    try:
        # Run pytest
        result = subprocess.run(
            ['pytest', 'tests/', '-v', '--tb=short'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("\n✓ All tests passed")
            return True
        else:
            print(f"\n✗ Some tests failed (exit code: {result.returncode})")
            print(result.stderr)
            return False
    
    except subprocess.TimeoutExpired:
        print("✗ Tests timed out after 5 minutes")
        return False
    except FileNotFoundError:
        print("✗ pytest not found - please install: pip install pytest")
        return False
    except Exception as e:
        print(f"✗ Failed to run tests: {e}")
        return False

def main():
    """Main verification function"""
    print("=" * 60)
    print("OpenClass Nexus AI - System Verification")
    print("=" * 60)
    
    results = {}
    
    # Check each phase
    results['Phase 0'] = check_phase_0()
    results['Phase 1'] = check_phase_1()
    results['Phase 2'] = check_phase_2()
    results['Phase 3'] = check_phase_3()
    results['Phase 4'] = check_phase_4()
    results['Phase 5'] = check_phase_5()
    results['Phase 6'] = check_phase_6()
    
    # Run tests
    results['Tests'] = run_tests()
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    for phase, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{phase:20s} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL PHASES VERIFIED SUCCESSFULLY")
        print("=" * 60)
        print("\nSystem is ready for use!")
        print("Start the server with: python api_server.py")
    else:
        print("✗ SOME PHASES FAILED VERIFICATION")
        print("=" * 60)
        print("\nPlease fix the issues above before proceeding.")
    print()
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
