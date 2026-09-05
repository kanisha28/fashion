# Production Dockerfile for Fashion Local Event Intelligence Platform
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Seed initial database and models
RUN python data/seed_data.py

EXPOSE 8000 8501

CMD ["python", "run.py"]
