FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update || (sleep 5 && apt-get update) \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file for caching
COPY backend/requirements.txt .

# Set environment variable for CPU-only PyTorch. This is already correctly placed.
ENV TORCH_INDEX_URL="https://download.pytorch.org/whl/cpu"

# --- Install core dependencies (excluding potentially heavy ones like sentence-transformers, chromadb, huggingface-hub) ---
# This step installs the majority of your requirements that are generally smaller and less complex.
RUN cat requirements.txt | grep -vE "sentence-transformers|chromadb|huggingface-hub" > /tmp/requirements_core.txt && \
    pip install --no-cache-dir -r /tmp/requirements_core.txt && \
    rm /tmp/requirements_core.txt

# --- Install chromadb separately ---
# Installing chromadb in its own step. It can involve C++ compilation.
RUN pip install --no-cache-dir chromadb==0.4.22

# --- Install sentence-transformers and huggingface-hub ---
# These packages often have large downloads (especially sentence-transformers with its PyTorch dependency).
# The TORCH_INDEX_URL environment variable from above will apply to this step.
RUN pip install --no-cache-dir sentence-transformers==2.2.2 huggingface-hub==0.10.0

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
