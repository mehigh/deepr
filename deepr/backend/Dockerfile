# Use official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# gcc and libpq-dev are often needed for psycopg2 (Postgres)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Install uvicorn explicitly if not in requirements (it was, but safe to ensure)
RUN pip install uvicorn[standard] psycopg2-binary

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${BACKEND_PORT:-8000}"]
