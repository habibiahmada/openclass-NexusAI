#!/usr/bin/env python3
"""
Database Initialization Script
OpenClass Nexus AI - Architecture Alignment Refactoring

This script initializes the PostgreSQL database with the schema and optional seed data.

Usage:
    python database/init_database.py --create-db
    python database/init_database.py --apply-schema
    python database/init_database.py --seed-data
    python database/init_database.py --all
"""

import argparse
import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import hashlib
from datetime import datetime, timedelta


def get_db_config():
    """Get database configuration from environment variables."""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'nexusai_db'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'root')
    }


def create_database(db_name='nexusai_db'):
    """Create the database if it doesn't exist."""
    config = get_db_config()
    
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
            print(f"✓ Database '{db_name}' already exists")
        else:
            # Create database
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(db_name)
            ))
            print(f"✓ Database '{db_name}' created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error creating database: {e}")
        return False


def apply_schema():
    """Apply the SQL schema to the database."""
    config = get_db_config()
    schema_file = Path(__file__).parent / 'schema.sql'
    
    if not schema_file.exists():
        print(f"✗ Schema file not found: {schema_file}")
        return False
    
    try:
        # Connect to nexusai database
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Read and execute schema
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✓ Schema applied successfully")
        
        # Verify tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"✓ Created {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error applying schema: {e}")
        return False


def hash_password(password):
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def seed_data():
    """Insert seed data for testing and development."""
    config = get_db_config()
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        print("Seeding database with initial data...")
        
        # 1. Create admin user
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, full_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
            RETURNING id
        """, ('admin', hash_password('admin123'), 'admin', 'Administrator'))
        
        admin_result = cursor.fetchone()
        if admin_result:
            print(f"✓ Created admin user (id: {admin_result[0]})")
        else:
            print("✓ Admin user already exists")
        
        # 2. Create sample teacher
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, full_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
            RETURNING id
        """, ('guru1', hash_password('guru123'), 'guru', 'Budi Santoso'))
        
        teacher_result = cursor.fetchone()
        if teacher_result:
            print(f"✓ Created teacher user (id: {teacher_result[0]})")
        else:
            print("✓ Teacher user already exists")
        
        # 3. Create sample student
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, full_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
            RETURNING id
        """, ('siswa1', hash_password('siswa123'), 'siswa', 'Ani Wijaya'))
        
        student_result = cursor.fetchone()
        if student_result:
            student_id = student_result[0]
            print(f"✓ Created student user (id: {student_id})")
        else:
            print("✓ Student user already exists")
            cursor.execute("SELECT id FROM users WHERE username = 'siswa1'")
            student_id = cursor.fetchone()[0]
        
        # 4. Create subjects
        subjects_data = [
            (10, 'Matematika', 'MAT_10'),
            (11, 'Matematika', 'MAT_11'),
            (12, 'Matematika', 'MAT_12'),
            (10, 'Informatika', 'INF_10'),
            (11, 'Informatika', 'INF_11'),
            (12, 'Informatika', 'INF_12'),
        ]
        
        subject_ids = {}
        for grade, name, code in subjects_data:
            cursor.execute("""
                INSERT INTO subjects (grade, name, code)
                VALUES (%s, %s, %s)
                ON CONFLICT (code) DO NOTHING
                RETURNING id
            """, (grade, name, code))
            
            result = cursor.fetchone()
            if result:
                subject_ids[code] = result[0]
                print(f"✓ Created subject: {name} Kelas {grade} ({code})")
            else:
                cursor.execute("SELECT id FROM subjects WHERE code = %s", (code,))
                subject_ids[code] = cursor.fetchone()[0]
        
        # 5. Create sample books
        cursor.execute("""
            INSERT INTO books (subject_id, title, filename, vkp_version, chunk_count)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            subject_ids.get('MAT_10'),
            'Matematika Kelas 10 Semester 1',
            'matematika_10_s1.pdf',
            '1.0.0',
            0
        ))
        print("✓ Created sample book")
        
        # 6. Create sample practice questions
        practice_questions = [
            (subject_ids.get('MAT_10'), 'Aljabar', 'easy', 
             'Selesaikan persamaan: 2x + 5 = 15', 'x = 5'),
            (subject_ids.get('MAT_10'), 'Geometri', 'medium',
             'Hitung luas segitiga dengan alas 10 cm dan tinggi 8 cm', 'Luas = 40 cm²'),
            (subject_ids.get('INF_10'), 'Pemrograman', 'easy',
             'Apa output dari: print(2 + 3 * 4)?', '14'),
        ]
        
        for subject_id, topic, difficulty, question, answer in practice_questions:
            if subject_id:
                cursor.execute("""
                    INSERT INTO practice_questions (subject_id, topic, difficulty, question_text, answer_hint)
                    VALUES (%s, %s, %s, %s, %s)
                """, (subject_id, topic, difficulty, question, answer))
        
        print(f"✓ Created {len(practice_questions)} practice questions")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✓ Database seeded successfully!")
        print("\nTest Credentials:")
        print("  Admin:   username=admin,  password=admin123")
        print("  Teacher: username=guru1,  password=guru123")
        print("  Student: username=siswa1, password=siswa123")
        
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error seeding data: {e}")
        return False


def verify_installation():
    """Verify database installation."""
    config = get_db_config()
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        print("\nVerifying database installation...")
        
        # Check tables
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]
        print(f"✓ Tables: {table_count}/8")
        
        # Check indexes
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE schemaname = 'public'
        """)
        index_count = cursor.fetchone()[0]
        print(f"✓ Indexes: {index_count}")
        
        # Check users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✓ Users: {user_count}")
        
        # Check subjects
        cursor.execute("SELECT COUNT(*) FROM subjects")
        subject_count = cursor.fetchone()[0]
        print(f"✓ Subjects: {subject_count}")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Database verification complete!")
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error verifying database: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Initialize OpenClass Nexus AI database'
    )
    parser.add_argument(
        '--create-db',
        action='store_true',
        help='Create the database'
    )
    parser.add_argument(
        '--apply-schema',
        action='store_true',
        help='Apply the SQL schema'
    )
    parser.add_argument(
        '--seed-data',
        action='store_true',
        help='Insert seed data'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all steps (create, schema, seed)'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify database installation'
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    print("=" * 60)
    print("OpenClass Nexus AI - Database Initialization")
    print("=" * 60)
    print()
    
    success = True
    
    if args.all or args.create_db:
        print("Step 1: Creating database...")
        success = create_database() and success
        print()
    
    if args.all or args.apply_schema:
        print("Step 2: Applying schema...")
        success = apply_schema() and success
        print()
    
    if args.all or args.seed_data:
        print("Step 3: Seeding data...")
        success = seed_data() and success
        print()
    
    if args.verify or args.all:
        verify_installation()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Database initialization complete!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("✗ Database initialization failed!")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
