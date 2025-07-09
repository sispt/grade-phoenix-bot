#!/bin/bash
set -e

echo "🚀 Starting predeploy script..."

# Install dependencies if needed
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set up environment
echo "🔧 Setting up environment..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run database migration
echo "🗄️ Running database migrations..."
alembic upgrade head

echo "✅ Predeploy completed successfully!" 