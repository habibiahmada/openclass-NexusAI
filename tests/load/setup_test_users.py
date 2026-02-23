#!/usr/bin/env python3
"""
Setup Test Users for Load Testing

Creates test users in the database for load testing.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.init_database import DatabaseInitializer
from config.app_config import app_config


def create_test_users():
    """Create test users for load testing"""
    print("=" * 60)
    print("Creating Test Users for Load Testing")
    print("=" * 60)
    
    # Initialize database
    db_init = DatabaseInitializer(app_config.database_url)
    
    # Test users to create
    test_users = [
        {"username": "siswa1", "password": "password123", "role": "siswa", "full_name": "Test Student 1"},
        {"username": "siswa2", "password": "password123", "role": "siswa", "full_name": "Test Student 2"},
        {"username": "siswa3", "password": "password123", "role": "siswa", "full_name": "Test Student 3"},
        {"username": "siswa4", "password": "password123", "role": "siswa", "full_name": "Test Student 4"},
        {"username": "siswa5", "password": "password123", "role": "siswa", "full_name": "Test Student 5"},
    ]
    
    created_count = 0
    existing_count = 0
    
    for user_data in test_users:
        try:
            # Check if user exists
            existing_user = db_init.user_repo.get_user_by_username(user_data["username"])
            
            if existing_user:
                print(f"✓ User '{user_data['username']}' already exists")
                existing_count += 1
            else:
                # Create user
                user = db_init.user_repo.create_user(
                    username=user_data["username"],
                    password=user_data["password"],  # Will be hashed by repository
                    role=user_data["role"],
                    full_name=user_data["full_name"]
                )
                print(f"✅ Created user: {user_data['username']}")
                created_count += 1
                
        except Exception as e:
            print(f"❌ Error creating user {user_data['username']}: {e}")
    
    print()
    print("=" * 60)
    print(f"Summary:")
    print(f"  Created: {created_count}")
    print(f"  Already Existed: {existing_count}")
    print(f"  Total: {len(test_users)}")
    print("=" * 60)
    print()
    print("✅ Test users are ready for load testing!")
    print()
    print("You can now run load tests with:")
    print("  locust -f tests/load/locustfile.py --host=http://localhost:8000")


if __name__ == "__main__":
    try:
        create_test_users()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
