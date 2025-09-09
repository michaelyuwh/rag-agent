# Production Dockerfile for RAG Agent Enterprise Platform

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

# Copy project configuration files first for better caching
COPY pyproject.toml uv.lock LICENSE README.md ./

# Install Python dependencies using uv
RUN uv sync --frozen

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/vector_store data/chat_history

# Expose Streamlit port
EXPOSE 8501

# Set environment variables
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application using uv
CMD ["uv", "run", "streamlit", "run", "rag_agent/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
