# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for ChromaDB)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create a data directory if it doesn't exist (it should be copied, but just in case)
RUN mkdir -p data

# Expose the port used by Hugging Face Spaces
EXPOSE 7860

# Run the application
CMD ["python", "main.py"]
