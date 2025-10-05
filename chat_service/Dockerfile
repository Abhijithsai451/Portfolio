# Stage 1: Builder - for installing dependencies and compiling
FROM python:3.11-slim-bullseye AS builder

WORKDIR /app

# Install system dependencies needed for building Python packages (chromadb, numpy, etc.)
RUN apt-get update || (sleep 5 && apt-get update) \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file early to leverage Docker's layer caching
COPY chat_service/requirements.txt .

# Set environment variable for CPU-only PyTorch (important for smaller builds)
ENV TORCH_INDEX_URL="https://download.pytorch.org/whl/cpu"

# Install all Python dependencies.
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - for running the chat application
FROM python:3.11-slim

WORKDIR /app

# Copy only the installed Python packages from the builder stage's user site-packages
COPY --from=builder /root/.local /usr/local

# Set environment variables to ensure Python finds the installed packages
ENV PATH="/usr/local/bin:$PATH"
ENV PYTHONPATH="/usr/local/lib/python3.11/site-packages:$PYTHONPATH"

# Copy application code for the chat service
COPY chat_service/ ./chat_service/
COPY utils/ ./utils/
COPY .env ./

# Create non-root user
RUN useradd -m -u 1000 appuser
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs
# Create directories for ChromaDB and model cache, these will be mounted as volumes
RUN mkdir -p /app/chroma_db && chown -R appuser:appuser /app/chroma_db
RUN mkdir -p /app/.cache/torch/sentence_transformers && chown -R appuser:appuser /app/.cache/torch/sentence_transformers

USER appuser

# Expose port (internal port for the chat service)
EXPOSE 8001

# Health check (pointing to the chat service's health endpoint, though minimal here)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

# Start application
CMD ["uvicorn", "chat_service.main:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "info"]