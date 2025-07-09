# Multi-stage Docker build for Sean GPT
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY backend/requirements.txt backend/requirements.txt
COPY frontend/requirements.txt frontend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -r frontend/requirements.txt

# Copy application code
COPY backend/ backend/
COPY frontend/ frontend/
COPY launch_app.py .

# Create data directories
RUN mkdir -p backend/data/chroma_db
RUN mkdir -p backend/data/github_vault

# Health check
COPY backend/health_check.py backend/
RUN chmod +x backend/health_check.py

# Expose port
EXPOSE 8501

# Health check command
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python backend/health_check.py || exit 1

# Default command
CMD ["streamlit", "run", "frontend/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]