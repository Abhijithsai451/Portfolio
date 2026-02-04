import os
import time
import logging
import json
import re
import base64
from pathlib import Path
from typing import List, Optional, Any
import numpy as np
import openai
import redis
import chromadb
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from utils.monitor import Monitor

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

monitor = Monitor()
app = FastAPI(title="Portfolio AI Chat Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)
USE_VECTOR_DB = os.getenv("USE_VECTOR_DB", "true").lower() == "true"
KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", "data")

try:
    redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
    redis_client.ping()
except Exception:
    redis_client = None

chroma_client = None
collection = None
if USE_VECTOR_DB:
    try:
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        collection = chroma_client.get_or_create_collection("portfolio_knowledge")
    except Exception as e:
        logger.error(f"ChromaDB error: {e}")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None
    is_voice: bool = False

class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    processing_time: float
    audio: Optional[str] = None

def load_all_knowledge(directory: str) -> str:
    combined = []
    data_path = Path(directory)
    if not data_path.is_absolute():
        data_path = Path(__file__).parent / directory
    
    for file_path in list(data_path.glob("*.txt")) + list(data_path.glob("*.md")):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                combined.append(f"--- SOURCE: {file_path.name} ---\n{f.read().strip()}")
        except Exception as e:
            logger.error(f"Load error {file_path}: {e}")
    return "\n\n".join(combined)

def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current_chunk, current_len = [], [], 0
    for s in sentences:
        if current_len + len(s) > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = current_chunk[-2:] if len(current_chunk) > 3 else []
            current_len = sum(len(x) for x in current_chunk)
        current_chunk.append(s)
        current_len += len(s)
    if current_chunk: chunks.append(' '.join(current_chunk))
    return chunks

KNOWLEDGE_BASE = ""
knowledge_chunks = []

@app.on_event("startup")
async def startup_event():
    global KNOWLEDGE_BASE, knowledge_chunks
    KNOWLEDGE_BASE = load_all_knowledge(KNOWLEDGE_DIR)
    knowledge_chunks = chunk_text(KNOWLEDGE_BASE)
    if USE_VECTOR_DB and collection and collection.count() == 0:
        for i, chunk in enumerate(knowledge_chunks):
            emb = await generate_embedding(chunk)
            if emb:
                collection.add(documents=[chunk], embeddings=[emb], ids=[f"chunk_{i}"])

async def generate_embedding(text: str) -> List[float]:
    try:
        res = client.embeddings.create(input=text, model="text-embedding-3-small")
        return res.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        return []

async def find_relevant_context(query: str, top_k: int = 3) -> str:
    try:
        if USE_VECTOR_DB and collection:
            emb = await generate_embedding(query)
            res = collection.query(query_embeddings=[emb], n_results=top_k)
            return "\n\n".join(res['documents'][0]) if res['documents'] else ""
    except Exception as e:
        logger.error(f"Context error: {e}")
    return "\n\n".join(knowledge_chunks[:2])

async def generate_audio(text: str) -> Optional[str]:
    try:
        res = client.audio.speech.create(model="tts-1", voice="alloy", input=text)
        return base64.b64encode(res.content).decode('utf-8')
    except Exception:
        return None

async def chat_with_openai(messages: List[dict]) -> str:
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.3, max_tokens=400)
        return res.choices[0].message.content
    except Exception:
        return "Service unavailable."

@app.get("/api/health")
async def health_check():
    return {"status": "OK", "uptime": time.time() - app.start_time}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    start = time.time()
    monitor.increment_chat_requests("received")
    try:
        context = await find_relevant_context(chat_request.message)
        prompt = f"Assistant for Abhijith Sai.\nContext: {context}\nLimit: 4-5 sentences."
        if chat_request.is_voice: prompt += "\nVoice: 3 sentences."
        
        ans = await chat_with_openai([{"role": "system", "content": prompt}, {"role": "user", "content": chat_request.message}])
        audio = await generate_audio(ans) if chat_request.is_voice else None
        
        proc_time = time.time() - start
        monitor.increment_chat_requests("success")
        return ChatResponse(response=ans, session_id=chat_request.session_id, processing_time=proc_time, audio=audio)
    except Exception:
        monitor.increment_chat_requests("error")
        raise HTTPException(status_code=500, detail="Error")

app.start_time = time.time()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
