"""
Migrate Database Schema

Adds missing columns to topic_mastery table:
- avg_complexity (FLOAT)
- last_question_date (TIMESTAMP)
- updated_at (TIMESTAMP)

Removes unused columns:
- correct_count
- last_interaction
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

def migrate_schema():
    """Migrate database schema"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL not set in .env file")
        return False
    
    try:
        print("=" * 60)
        print("Database Schema Migration")
        print("=" * 60)
        print("\nConnecting to database...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'topic_mastery'
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"\nExisting columns: {', '.join(existing_columns)}")
        
        migrations = []
        
        # Add avg_complexity if not exists
        if 'avg_complexity' not in existing_columns:
            migrations.append(
                "ALTER TABLE topic_mastery ADD COLUMN avg_complexity FLOAT DEFAULT 0.0"
            )
            print("\n✓ Will add column: avg_complexity")
        else:
            print("\n✓ Column avg_complexity already exists")
        
        # Add last_question_date if not exists
        if 'last_question_date' not in existing_columns:
            migrations.append(
                "ALTER TABLE topic_mastery ADD COLUMN last_question_date TIMESTAMP"
            )
            print("✓ Will add column: last_question_date")
        else:
            print("✓ Column last_question_date already exists")
        
        # Add updated_at if not exists
        if 'updated_at' not in existing_columns:
            migrations.append(
                "ALTER TABLE topic_mastery ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )
            print("✓ Will add column: updated_at")
        else:
            print("✓ Column updated_at already exists")
        
        # Migrate data from old columns to new columns if needed
        if 'last_interaction' in existing_columns and 'last_question_date' not in existing_columns:
            migrations.append(
                "UPDATE topic_mastery SET last_question_date = last_interaction WHERE last_interaction IS NOT NULL"
            )
            print("✓ Will migrate data: last_interaction -> last_question_date")
        
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
            WHERE table_name = 'topic_mastery'
            ORDER BY ordinal_position
        """)
        
        print("\nFinal schema for topic_mastery:")
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
    success = migrate_schema()
    sys.exit(0 if success else 1)
