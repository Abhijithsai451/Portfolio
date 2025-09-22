# Stage 1: Builder - for installing dependencies and compiling
FROM python:3.11-slim-buster AS builder

WORKDIR /app

# Install system dependencies needed for building Python packages
# build-essential includes gcc, g++, and other necessary tools
RUN apt-get update || (sleep 5 && apt-get update) \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file early to leverage Docker's layer caching
COPY backend/requirements.txt .

# Set environment variable for CPU-only PyTorch (important for smaller builds)
ENV TORCH_INDEX_URL="https://download.pytorch.org/whl/cpu"

# Install all Python dependencies.
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - for running the application
FROM python:3.11-slim

WORKDIR /app

# Copy only the installed Python packages from the builder stage's user site-packages
COPY --from=builder /root/.local /usr/local

# Set environment variables to ensure Python finds the installed packages
ENV PATH="/usr/local/bin:$PATH"
ENV PYTHONPATH="/usr/local/lib/python3.11/site-packages:$PYTHONPATH"

# Copy application code. Ensure your .dockerignore is effective here!
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
