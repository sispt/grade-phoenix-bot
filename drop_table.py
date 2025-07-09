#!/usr/bin/env python3
"""
Script to drop the grades_failsafe table
"""
import os
import psycopg2

def main():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return 1
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Execute the DROP TABLE command
        cursor.execute("DROP TABLE IF EXISTS grades_failsafe;")
        
        # Commit the transaction
        conn.commit()
        
        print("✅ Successfully dropped grades_failsafe table (if it existed)")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 