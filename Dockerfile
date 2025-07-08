THIS SHOULD BE A LINTER ERRORFROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs backups

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./data/bot.db

# Expose port for webhook
EXPOSE 8443

# Run the bot
CMD ["python", "main.py"]