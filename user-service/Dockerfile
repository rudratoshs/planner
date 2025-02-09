FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create logs directory
RUN mkdir -p /app/logs

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Install the project in development mode
RUN pip install -e .

# Set permissions for logs directory
RUN chmod 777 /app/logs

RUN prisma generate

CMD ["sh", "-c", "prisma migrate deploy && python prisma/seed.py && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"]