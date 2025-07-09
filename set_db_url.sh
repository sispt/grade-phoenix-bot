#!/bin/bash
# Database URL export script for Alembic migrations
# Replace the URL below with your actual MySQL database URL (example shown for Railway)

export MYSQL_URL="mysql+pymysql://root:password@mainline.proxy.rlwy.net:3306/railway"
echo "✅ MYSQL_URL environment variable set for this session."
echo "You can now run Alembic commands like:"
echo "  .venv/bin/alembic revision --autogenerate -m 'Description'"
echo "  .venv/bin/alembic upgrade head" 