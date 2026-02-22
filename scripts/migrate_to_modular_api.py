"""
Migration Script: Migrate from monolithic api_server.py to modular structure

This script:
1. Backs up the old api_server.py
2. Replaces it with the new modular version
3. Verifies the new structure
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def main():
    print("=" * 60)
    print("OpenClass Nexus AI - API Server Migration")
    print("=" * 60)
    print()
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Paths
    old_api_server = project_root / "api_server.py"
    new_api_server = project_root / "api_server_new.py"
    backup_dir = project_root / "backups" / "api_migration"
    
    # Create backup directory
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Backup old api_server.py
    if old_api_server.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"api_server_backup_{timestamp}.py"
        
        print(f"[1/4] Backing up old api_server.py...")
        shutil.copy2(old_api_server, backup_file)
        print(f"      ✓ Backup created: {backup_file}")
    else:
        print(f"[1/4] No old api_server.py found, skipping backup")
    
    print()
    
    # Step 2: Replace with new modular version
    if new_api_server.exists():
        print(f"[2/4] Replacing api_server.py with modular version...")
        shutil.copy2(new_api_server, old_api_server)
        print(f"      ✓ api_server.py updated")
    else:
        print(f"[2/4] ERROR: api_server_new.py not found!")
        return
    
    print()
    
    # Step 3: Verify new structure
    print(f"[3/4] Verifying new modular structure...")
    
    required_files = [
        "src/api/__init__.py",
        "src/api/config.py",
        "src/api/models.py",
        "src/api/auth.py",
        "src/api/state.py",
        "src/api/routers/__init__.py",
        "src/api/routers/auth_router.py",
        "src/api/routers/chat_router.py",
        "src/api/routers/teacher_router.py",
        "src/api/routers/admin_router.py",
        "src/api/routers/pedagogy_router.py",
        "src/api/routers/queue_router.py",
        "src/api/routers/pages_router.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"      ✓ {file_path}")
        else:
            print(f"      ✗ {file_path} - MISSING!")
            all_exist = False
    
    print()
    
    # Step 4: Summary
    print(f"[4/4] Migration Summary")
    print()
    
    if all_exist:
        print("      ✓ All modular files are in place")
        print("      ✓ Migration completed successfully!")
        print()
        print("Next steps:")
        print("  1. Review .env file and add missing configurations")
        print("  2. Test the server: python api_server.py")
        print("  3. If everything works, you can delete api_server_new.py")
    else:
        print("      ✗ Some files are missing!")
        print("      Please check the error messages above")
        print()
        print("To restore old version:")
        print(f"  cp {backup_file} api_server.py")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
