# Dockerfile for FastAPI + Uvicorn + requirements
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies (for opencv, dlib, etc.)
RUN apt-get update && \
    apt-get install -y build-essential cmake libglib2.0-0 libsm6 libxrender1 libxext6 libgtk2.0-dev pkg-config libboost-all-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port

# Run the app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]