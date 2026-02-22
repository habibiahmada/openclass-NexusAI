"""
Migrate practice_questions Table

Renames columns to match code expectations:
- 'question' → 'question_text'
- 'answer' → 'answer_hint'
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

def migrate_practice_questions():
    """Migrate practice_questions table schema"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL not set in .env file")
        return False
    
    try:
        print("=" * 60)
        print("Practice Questions Table Migration")
        print("=" * 60)
        print("\nConnecting to database...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'practice_questions'
            ORDER BY ordinal_position
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"\nExisting columns: {', '.join(existing_columns)}")
        
        migrations = []
        
        # Check if we need to rename 'question' to 'question_text'
        if 'question' in existing_columns and 'question_text' not in existing_columns:
            migrations.append(
                "ALTER TABLE practice_questions RENAME COLUMN question TO question_text"
            )
            print("\n✓ Will rename: question → question_text")
        elif 'question_text' in existing_columns:
            print("\n✓ Column 'question_text' already exists")
        elif 'question' not in existing_columns and 'question_text' not in existing_columns:
            migrations.append(
                "ALTER TABLE practice_questions ADD COLUMN question_text TEXT NOT NULL DEFAULT ''"
            )
            print("\n✓ Will add column: question_text")
        
        # Check if we need to rename 'answer' to 'answer_hint'
        if 'answer' in existing_columns and 'answer_hint' not in existing_columns:
            migrations.append(
                "ALTER TABLE practice_questions RENAME COLUMN answer TO answer_hint"
            )
            print("✓ Will rename: answer → answer_hint")
        elif 'answer_hint' in existing_columns:
            print("✓ Column 'answer_hint' already exists")
        elif 'answer' not in existing_columns and 'answer_hint' not in existing_columns:
            migrations.append(
                "ALTER TABLE practice_questions ADD COLUMN answer_hint TEXT NOT NULL DEFAULT ''"
            )
            print("✓ Will add column: answer_hint")
        
        # Execute migrations
        if migrations:
            print(f"\nExecuting {len(migrations)} migration(s)...")
            for i, migration in enumerate(migrations, 1):
                print(f"\n{i}. {migration}")
                cursor.execute(migration)
            
            conn.commit()
            print("\n✓ All migrations completed successfully")
        else:
            print("\n✓ No migrations needed - schema is up to date")
        
        # Verify final schema
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'practice_questions'
            ORDER BY ordinal_position
        """)
        
        print("\nFinal schema for practice_questions:")
        for column_name, data_type in cursor.fetchall():
            print(f"  - {column_name:25s} {data_type}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print()
        
        return True
        
    except Exception as e:
        print(f"\nERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_practice_questions()
    sys.exit(0 if success else 1)
