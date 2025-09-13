#!/bin/bash

echo "Starting Portfolio AI Backend"
echo "Make Sure Ollama is running at http://localhost:11434"
echo "Available Models: llama3.1 and nomic-embed-text"

# Checking if knowledge base file exists.
if [ ! -f "knowledge_base.txt"]; then
  echo "Warning: Knowledge_base.txt not found. Creating default file..."
  echo "Creating default knowledge base file. Please update it with your actual information."
    cat > knowledge_base.txt << EOF
ABHIJITH SAI - MATHEMATICIAN & DATA SCIENTIST

Professional Summary:
Experienced data scientist with strong mathematical background...

Technical Skills:
- Python, R, Machine Learning, Statistical Analysis

Projects:
- Various data science and machine learning projects

Contact: tsaiabhi.cool@gmail.com
EOF
fi

# Install dependencies if needed.
if [ ! -d "venv"]; then
  echo "Creating virtual environment...."
  python 3 =m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
else
  source venv/bin/activate
fi

# Start the Server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

