FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# RUN apt-get update && apt-get install -y \
#    gcc \
#    g++ \
#    && rm -rf /var/lib/apt/lists/*
RUN apt-get update || (sleep 5 && apt-get update) \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*


# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
ENV TORCH_INDEX_URL="https://download.pytorch.org/whl/cpu"


RUN pip install -r requirements.txt

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