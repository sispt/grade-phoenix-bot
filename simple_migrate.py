#!/usr/bin/env python3
"""
Migrate users from old PostgreSQL ($DATABASE_URL) to MySQL ($MYSQL_URL), copying only columns that exist in the current MySQL users table.
"""
import os
import sys
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Get environment variables
PG_URL = os.getenv("DATABASE_URL")
MYSQL_URL = os.getenv("MYSQL_URL")

if not PG_URL or not MYSQL_URL:
    print("❌ Both DATABASE_URL (PostgreSQL) and MYSQL_URL (MySQL) must be set in the environment.")
    sys.exit(1)

# Ensure MySQL URL uses correct dialect
if MYSQL_URL.startswith("mysql://"):
    MYSQL_URL = MYSQL_URL.replace("mysql://", "mysql+pymysql://", 1)

# Connect to PostgreSQL (source)
pg_engine = create_engine(PG_URL)
pg_meta = MetaData()
pg_meta.reflect(pg_engine, only=['users'])
pg_users = pg_meta.tables['users']

# Connect to MySQL (target)
mysql_engine = create_engine(MYSQL_URL)
mysql_meta = MetaData()
mysql_meta.reflect(mysql_engine, only=['users'])
mysql_users = mysql_meta.tables['users']

# Find common columns
pg_columns = set(pg_users.columns.keys())
mysql_columns = set(mysql_users.columns.keys())
shared_columns = list(pg_columns & mysql_columns)
print(f"🔗 Shared columns: {shared_columns}")

# Prepare sessions
PGSession = sessionmaker(bind=pg_engine)
MySQLSession = sessionmaker(bind=mysql_engine)

pg_session = PGSession()
mysql_session = MySQLSession()

try:
    # Fetch all users from PostgreSQL
    users = pg_session.execute(select(pg_users)).fetchall()
    print(f"👥 Found {len(users)} users in PostgreSQL.")
    migrated = 0
    for user_row in users:
        user_dict = {col: user_row._mapping[col] for col in shared_columns}
        # Build insert statement with ON DUPLICATE KEY UPDATE for MySQL
        insert_stmt = mysql_users.insert().values(**user_dict)
        # SQLAlchemy's on_duplicate_key_update is only available in 1.4+ and for MySQL
        # If not available, fallback to raw SQL
        try:
            from sqlalchemy.dialects.mysql import insert as mysql_insert
            upsert_stmt = mysql_insert(mysql_users).values(**user_dict)
            update_dict = {col: user_dict[col] for col in shared_columns if col != 'username'}
            upsert_stmt = upsert_stmt.on_duplicate_key_update(**update_dict)
            mysql_session.execute(upsert_stmt)
        except ImportError:
            # Fallback: try normal insert, ignore duplicates
            try:
                mysql_session.execute(insert_stmt)
            except SQLAlchemyError as e:
                if 'Duplicate entry' in str(e):
                    pass  # Ignore duplicate
                else:
                    print(f"❌ Failed to insert user {user_dict.get('username')}: {e}")
                    continue
        migrated += 1
    mysql_session.commit()
    print(f"✅ Migrated {migrated} users to MySQL.")
except Exception as e:
    print(f"❌ Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    pg_session.close()
    mysql_session.close() 