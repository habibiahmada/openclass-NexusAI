"""
Migrate weak_areas Table

Renames column from 'recommended_practice' to 'recommendation'
to match the code expectations.
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

def migrate_weak_areas():
    """Migrate weak_areas table schema"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL not set in .env file")
        return False
    
    try:
        print("=" * 60)
        print("Weak Areas Table Migration")
        print("=" * 60)
        print("\nConnecting to database...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'weak_areas'
            ORDER BY ordinal_position
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"\nExisting columns: {', '.join(existing_columns)}")
        
        migrations = []
        
        # Check if we need to rename recommended_practice to recommendation
        if 'recommended_practice' in existing_columns and 'recommendation' not in existing_columns:
            migrations.append(
                "ALTER TABLE weak_areas RENAME COLUMN recommended_practice TO recommendation"
            )
            print("\n✓ Will rename: recommended_practice → recommendation")
        elif 'recommendation' in existing_columns:
            print("\n✓ Column 'recommendation' already exists")
        elif 'recommended_practice' not in existing_columns and 'recommendation' not in existing_columns:
            # Neither column exists, add recommendation
            migrations.append(
                "ALTER TABLE weak_areas ADD COLUMN recommendation TEXT"
            )
            print("\n✓ Will add column: recommendation")
        
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
            WHERE table_name = 'weak_areas'
            ORDER BY ordinal_position
        """)
        
        print("\nFinal schema for weak_areas:")
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
    success = migrate_weak_areas()
    sys.exit(0 if success else 1)
