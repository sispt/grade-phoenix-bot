#!/bin/bash
# Database URL export script for Alembic migrations
# Replace the URL below with your actual Railway database URL

export DATABASE_URL="postgresql://postgres:BdKehwAqWYaDgngmlbEukzwFOxUpSMVV@mainline.proxy.rlwy.net:32884/railway"
echo "✅ DATABASE_URL environment variable set for this session."
echo "You can now run Alembic commands like:"
echo "  .venv/bin/alembic revision --autogenerate -m 'Description'"
echo "  .venv/bin/alembic upgrade head" 