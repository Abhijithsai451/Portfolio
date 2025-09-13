import os
import re
from typing import List

import numpy as np
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables
load_dotenv()

app = FastAPI(title="Portfolio AI Agent", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.1")
KNOWLEDGE_BASE_FILE = os.getenv("KNOWLEDGE_BASE_URL", "/knowledge_base.txt")


# Pydantic models
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


class HealthResponse(BaseModel):
    status: str
    message: str


# Load Knowledge base from a file
def load_knowledge_base(file_path: str) -> str:
    """Load knowledge base from a file"""
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Warning - Knowledge base file not found {file_path}. Using default knowledge base.")
        return """Abhijith Sai is a Mathematician and Data Scientist with expertise in:
                    - Python and R programming
                    - Machine Learning algorithms
                    - Statistical Analysis
                    - Data Visualization
                    - Big Data technologies"""
    except Exception as e:
        print(f"Error loading knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Failed to load knowledge base")
        return ""


# Knowledge base - Enhanced with your portfolio data
KNOWLEDGE_BASE = load_knowledge_base(KNOWLEDGE_BASE_FILE)


def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """Split text into manageable chunks"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(sentence)
        current_length += sentence_length

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


# Chunk the knowledge base
knowledge_chunks = chunk_text(KNOWLEDGE_BASE)


async def generate_embedding(text: str) -> List[float]:
    """Generate text embedding using Ollama"""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": text
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("embedding", [])
    except Exception as e:
        print(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embedding")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


async def find_relevant_context(query: str, top_k: int = 3) -> str:
    """Find most relevant context from knowledge base"""
    try:
        query_embedding = await generate_embedding(query)

        similarities = []
        for chunk in knowledge_chunks:
            chunk_embedding = await generate_embedding(chunk)
            similarity = cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((chunk, similarity))

        # Sort by similarity and get top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        relevant_chunks = [chunk for chunk, score in similarities[:top_k] if score > 0.1]

        return "\n\n".join(relevant_chunks) if relevant_chunks else KNOWLEDGE_BASE[:1000]

    except Exception as e:
        print(f"Error finding relevant context: {e}")
        return KNOWLEDGE_BASE[:1000]  # Fallback to first part of knowledge base


async def chat_with_ollama(messages: List[dict]) -> str:
    """Send chat request to Ollama"""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": CHAT_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "Sorry, I couldn't generate a response.")

    except Exception as e:
        print(f"Error chatting with Ollama: {e}")
        raise HTTPException(status_code=500, detail="Failed to get response from AI")


@app.get("/", response_model=HealthResponse)
async def root():
    return {"status": "OK", "message": "Portfolio AI Agent is running"}


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return {"status": "OK", "message": "Server is healthy"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Find relevant context
        context = await find_relevant_context(request.message)

        # Prepare system prompt
        system_prompt = f"""You are an AI assistant representing Abhijith Sai, a Mathematician and Data Scientist. 
        Use the following information about Abhijith to answer questions accurately and helpfully. 
        Be professional, friendly, and concise.

        ABOUT ABHIJITH:
        {context}

        IMPORTANT INSTRUCTIONS:
        1. ONLY use the information provided above about Abhijith
        2. Be honest if you don't know something - say "I don't have that information about Abhijith"
        3. Keep responses focused on skills, projects, and experience
        4. Be specific about technologies and outcomes when possible
        5. If asked about contact information, provide what's available
        6. Never make up or hallucinate information
        7. If the question is not about Abhijith, politely redirect
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message}
        ]

        # Get response from Ollama
        response = await chat_with_ollama(messages)

        return ChatResponse(response=response)

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
