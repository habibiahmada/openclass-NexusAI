"""
Setup Database Script

This script:
1. Creates PostgreSQL database if not exists
2. Runs schema.sql to create all tables
3. Seeds initial data (subjects for informatika kelas 10)
4. Verifies all tables are created correctly
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL not set in .env file")
        print("Please set DATABASE_URL=postgresql://user:password@localhost:5432/nexusai")
        return False
    
    # Parse database URL to get connection params
    # Format: postgresql://user:password@host:port/database
    try:
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 5432
        database = parsed.path[1:]  # Remove leading /
        
        print(f"Connecting to PostgreSQL at {host}:{port}...")
        
        # Connect to postgres database to create our database
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (database,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database '{database}'...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(database)
            ))
            print(f"✓ Database '{database}' created successfully")
        else:
            print(f"✓ Database '{database}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create database: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running")
        print("2. DATABASE_URL is correct in .env file")
        print("3. User has permission to create databases")
        return False

def run_schema():
    """Run schema.sql to create all tables"""
    database_url = os.getenv('DATABASE_URL')
    
    try:
        print("\nCreating database schema...")
        
        # Read schema file
        schema_file = project_root / 'database' / 'schema.sql'
        if not schema_file.exists():
            print(f"ERROR: Schema file not found: {schema_file}")
            return False
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Connect and execute schema
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Execute schema (may contain multiple statements)
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✓ Database schema created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.errors.DuplicateTable as e:
        print("✓ Tables already exist (skipping creation)")
        return True
    except Exception as e:
        print(f"ERROR: Failed to create schema: {e}")
        return False

def seed_initial_data():
    """Seed initial data (subjects)"""
    database_url = os.getenv('DATABASE_URL')
    
    try:
        print("\nSeeding initial data...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Insert informatika kelas 10 subject
        cursor.execute("""
            INSERT INTO subjects (grade, name, code)
            VALUES (10, 'Informatika', 'INF_10')
            ON CONFLICT (code) DO NOTHING
            RETURNING id
        """)
        
        result = cursor.fetchone()
        if result:
            subject_id = result[0]
            print(f"✓ Created subject: Informatika Kelas 10 (ID: {subject_id})")
        else:
            # Subject already exists, get its ID
            cursor.execute("SELECT id FROM subjects WHERE code = 'INF_10'")
            subject_id = cursor.fetchone()[0]
            print(f"✓ Subject already exists: Informatika Kelas 10 (ID: {subject_id})")
        
        # Insert sample book for informatika
        cursor.execute("""
            INSERT INTO books (subject_id, title, filename, vkp_version, chunk_count)
            VALUES (%s, 'Informatika Kelas 10', 'informatika_kelas_10.pdf', '1.0.0', 0)
            ON CONFLICT DO NOTHING
        """, (subject_id,))
        
        conn.commit()
        print("✓ Initial data seeded successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to seed data: {e}")
        return False

def verify_tables():
    """Verify all required tables exist"""
    database_url = os.getenv('DATABASE_URL')
    
    required_tables = [
        'users',
        'sessions',
        'subjects',
        'books',
        'chat_history',
        'topic_mastery',
        'weak_areas',
        'practice_questions'
    ]
    
    try:
        print("\nVerifying database tables...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        all_exist = True
        for table in required_tables:
            if table in existing_tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} (MISSING)")
                all_exist = False
        
        cursor.close()
        conn.close()
        
        if all_exist:
            print("\n✓ All required tables exist")
            return True
        else:
            print("\n✗ Some tables are missing")
            return False
        
    except Exception as e:
        print(f"ERROR: Failed to verify tables: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("OpenClass Nexus AI - Database Setup")
    print("=" * 60)
    
    # Step 1: Create database
    if not create_database_if_not_exists():
        print("\n✗ Database setup failed")
        return False
    
    # Step 2: Run schema
    if not run_schema():
        print("\n✗ Schema creation failed")
        return False
    
    # Step 3: Seed initial data
    if not seed_initial_data():
        print("\n✗ Data seeding failed")
        return False
    
    # Step 4: Verify tables
    if not verify_tables():
        print("\n✗ Table verification failed")
        return False
    
    print("\n" + "=" * 60)
    print("✓ Database setup completed successfully!")
    print("=" * 60)
    print("\nYou can now start the API server:")
    print("  python api_server.py")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
