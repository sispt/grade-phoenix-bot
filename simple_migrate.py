#!/usr/bin/env python3
"""
Simple migration script that directly executes SQL to fix the telegram_id column
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

def parse_database_url(database_url):
    """Parse database URL and return connection parameters"""
    from urllib.parse import urlparse
    
    # Handle different URL formats
    if database_url.startswith('mysql+pymysql://'):
        # Remove the pymysql part for parsing
        clean_url = database_url.replace('mysql+pymysql://', 'mysql://')
    elif database_url.startswith('mysql://'):
        clean_url = database_url
    else:
        # Assume it's a raw MySQL URL
        clean_url = f'mysql://{database_url}'
    
    parsed = urlparse(clean_url)
    
    return {
        'host': parsed.hostname,
        'port': parsed.port or 3306,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/')
    }

def run_simple_migration():
    """Run a simple migration to fix the telegram_id column"""
    try:
        import pymysql
        
        # Get database URL
        database_url = os.getenv("MYSQL_URL")
        if not database_url:
            print("❌ MYSQL_URL environment variable not set")
            return False
            
        # Parse the URL
        conn_params = parse_database_url(database_url)
        
        print(f"🔌 Connecting to MySQL at {conn_params['host']}:{conn_params['port']}")
        
        # Connect to database
        connection = pymysql.connect(
            host=conn_params['host'],
            port=conn_params['port'],
            user=conn_params['user'],
            password=conn_params['password'],
            database=conn_params['database'],
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
            """, (conn_params['database'],))
            
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
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_simple_migration()
    sys.exit(0 if success else 1) 