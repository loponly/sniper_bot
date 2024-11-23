FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including git-lfs
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

# Initialize git-lfs
RUN git lfs install

# Install PyTorch and other dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories
RUN mkdir -p /app/models

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/models
ENV HF_HOME=/app/models

# Run the agent
CMD ["python", "main.py"] 