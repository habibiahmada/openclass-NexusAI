#!/usr/bin/env python3
"""
Test Database Setup Script

This script sets up a PostgreSQL test database for running property-based tests.
It creates the database, applies the schema, and verifies the setup.

Usage:
    python tests/setup_test_database.py
    
Environment Variables:
    TEST_DB_HOST     - Database host (default: localhost)
    TEST_DB_PORT     - Database port (default: 5432)
    TEST_DB_NAME     - Test database name (default: nexusai_test)
    TEST_DB_USER     - Database user (default: postgres)
    TEST_DB_PASSWORD - Database password (default: postgres)
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_test_db_config():
    """Get test database configuration from environment variables."""
    return {
        'host': os.getenv('TEST_DB_HOST', '127.0.0.1'),
        'port': os.getenv('TEST_DB_PORT', '5432'),
        'database': os.getenv('TEST_DB_NAME', 'nexusai_test'),
        'user': os.getenv('TEST_DB_USER', 'root'),
        'password': os.getenv('TEST_DB_PASSWORD', 'root')
    }


def create_test_database():
    """Create the test database if it doesn't exist."""
    config = get_test_db_config()
    db_name = config['database']
    
    print(f"Creating test database '{db_name}'...")
    
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database='postgres',
            user=config['user'],
            password=config['password']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone()
        
        if exists:
            print(f"  ✓ Database '{db_name}' already exists")
        else:
            # Create database
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(db_name)
            ))
            print(f"  ✓ Database '{db_name}' created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"  ✗ Error creating database: {e}")
        return False


def apply_schema():
    """Apply the SQL schema to the test database."""
    config = get_test_db_config()
    
    # Find schema file
    project_root = Path(__file__).parent.parent
    schema_file = project_root / 'database' / 'schema.sql'
    
    if not schema_file.exists():
        print(f"  ✗ Schema file not found: {schema_file}")
        return False
    
    print(f"Applying schema from {schema_file}...")
    
    try:
        # Connect to test database
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Read and execute schema
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        conn.commit()
        
        print("  ✓ Schema applied successfully")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"  ✓ Created {len(tables)} tables:")
        for table in tables:
            print(f"    - {table[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"  ✗ Error applying schema: {e}")
        return False


def verify_setup():
    """Verify the test database is set up correctly."""
    config = get_test_db_config()
    
    print("Verifying test database setup...")
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Check required tables exist
        required_tables = [
            'users', 'sessions', 'chat_history', 
            'subjects', 'books', 'topic_mastery',
            'weak_areas', 'practice_questions'
        ]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = set(required_tables) - set(existing_tables)
        
        if missing_tables:
            print(f"  ✗ Missing tables: {', '.join(missing_tables)}")
            return False
        
        print(f"  ✓ All {len(required_tables)} required tables exist")
        
        # Test basic operations
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            print("  ✓ Database connection working")
        else:
            print("  ✗ Database connection test failed")
            return False
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"  ✗ Verification failed: {e}")
        return False


def print_connection_string():
    """Print the TEST_DATABASE_URL connection string."""
    config = get_test_db_config()
    
    connection_string = (
        f"postgresql://{config['user']}:{config['password']}"
        f"@{config['host']}:{config['port']}/{config['database']}"
    )
    
    print("\n" + "="*70)
    print("Test Database Setup Complete!")
    print("="*70)
    print("\nTo run the property tests, set the environment variable:")
    print("\nWindows PowerShell:")
    print(f'  $env:TEST_DATABASE_URL="{connection_string}"')
    print("\nWindows CMD:")
    print(f'  set TEST_DATABASE_URL={connection_string}')
    print("\nLinux/Mac:")
    print(f'  export TEST_DATABASE_URL="{connection_string}"')
    print("\nThen run the tests:")
    print("  pytest tests/property/test_data_persistence.py -v")
    print("="*70 + "\n")


def main():
    """Main setup function."""
    print("\n" + "="*70)
    print("Test Database Setup for Property-Based Tests")
    print("="*70 + "\n")
    
    # Step 1: Create database
    if not create_test_database():
        print("\n✗ Failed to create test database")
        sys.exit(1)
    
    # Step 2: Apply schema
    if not apply_schema():
        print("\n✗ Failed to apply schema")
        sys.exit(1)
    
    # Step 3: Verify setup
    if not verify_setup():
        print("\n✗ Failed to verify setup")
        sys.exit(1)
    
    # Step 4: Print connection string
    print_connection_string()
    
    print("✓ Test database setup completed successfully!\n")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
