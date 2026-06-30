FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies needed for compiling python packages, geoalchemy (GEOS, GDAL, PROJ), etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ./backend ./backend
COPY ./ai_engine ./ai_engine
COPY ./database ./database

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Start server using uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
