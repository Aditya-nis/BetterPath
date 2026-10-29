# Production-ready Dockerfile for AI-Based Route Optimization TSP System
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python packages
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app/

# Expose standard Django port
EXPOSE 8000

# Startup command: apply database migrations, seed sample cities, and run server
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py seed_cities && python manage.py runserver 0.0.0.0:8000"]
