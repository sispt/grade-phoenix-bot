#!/usr/bin/env python3
"""
Simple migration script that directly executes SQL to fix the telegram_id column
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

def run_simple_migration():
    """Run a simple migration to fix the telegram_id column"""
    try:
        import pymysql
        from urllib.parse import urlparse
        
        # Get database URL
        database_url = os.getenv("MYSQL_URL")
        if not database_url:
            print("❌ MYSQL_URL environment variable not set")
            return False
            
        # Parse the URL
        parsed = urlparse(database_url)
        
        # Extract connection details
        host = parsed.hostname
        port = parsed.port or 3306
        username = parsed.username
        password = parsed.password
        database = parsed.path.lstrip('/')
        
        print(f"🔌 Connecting to MySQL at {host}:{port}")
        
        # Connect to database
        connection = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Check if the column exists and its current type
            cursor.execute("""
                SELECT COLUMN_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'telegram_id'
            """, (database,))
            
            result = cursor.fetchone()
            if result:
                current_type = result[0]
                print(f"📊 Current telegram_id column type: {current_type}")
                
                if 'bigint' not in current_type.lower():
                    print("🔧 Altering telegram_id column to BIGINT...")
                    cursor.execute("ALTER TABLE users MODIFY COLUMN telegram_id BIGINT")
                    connection.commit()
                    print("✅ Column altered successfully!")
                else:
                    print("✅ Column is already BIGINT, no changes needed")
            else:
                print("❌ telegram_id column not found in users table")
                return False
                
        connection.close()
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_simple_migration()
    sys.exit(0 if success else 1) 