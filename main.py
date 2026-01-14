import asyncio
import json
import logging
import os
import re
import time
import base64
import glob
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

import uvicorn
import aiohttp
import openai
import chromadb
from chromadb.config import Settings
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Import local monitor
try:
    from utils.monitor import Monitor
except ImportError:
    # Fallback if utils not properly structured
    class Monitor:
        def __init__(self): self.stats = {}
        def increment_chat_requests(self, status): pass
        def set_response_time(self, time): pass
        def get_stats(self): return {"avg_response_time": 0}

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Portfolio AI Agent",
              description="Unified Portfolio Website & AI Assistant",
              version="1.0.0")

# --- Middleware & Security ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Optimized for deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_VECTOR_DB = os.getenv("USE_VECTOR_DB", "true").lower() == "true"
KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", "data")

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found! AI features will be disabled.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)
monitor = Monitor()

# --- ChromaDB Setup ---
collection = None
if USE_VECTOR_DB:
    try:
        chroma_client = chromadb.Client(Settings(
            persist_directory="./chroma_db",
            anonymized_telemetry=False
        ))
        # Clear old data to ensure consistent dimensions
        try:
            chroma_client.delete_collection("portfolio_knowledge")
        except:
            pass
        collection = chroma_client.get_or_create_collection("portfolio_knowledge")
        logger.info("ChromaDB initialized.")
    except Exception as e:
        logger.error(f"ChromaDB error: {e}")

# --- AI & RAG Logic ---
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
    files = list(data_path.glob("*.txt")) + list(data_path.glob("*.md"))
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                combined.append(f"--- SOURCE: {f.name} ---\n{file.read().strip()}")
        except Exception as e:
            logger.error(f"Error loading {f.name}: {e}")
    return "\n\n".join(combined)

def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, curr, curr_len = [], [], 0
    for s in sentences:
        if curr_len + len(s) > chunk_size and curr:
            chunks.append(' '.join(curr))
            curr = curr[-2:] if len(curr) > 3 else []
            curr_len = sum(len(i) for i in curr)
        curr.append(s)
        curr_len += len(s)
    if curr: chunks.append(' '.join(curr))
    return chunks

# Initial Knowledge Load
KNOWLEDGE_BASE = load_all_knowledge(KNOWLEDGE_DIR)
knowledge_chunks = chunk_text(KNOWLEDGE_BASE)

if USE_VECTOR_DB and collection and knowledge_chunks:
    try:
        # Generate embeddings using OpenAI
        embeddings = []
        for chunk in knowledge_chunks:
            resp = client.embeddings.create(input=chunk, model="text-embedding-3-small")
            embeddings.append(resp.data[0].embedding)
        
        collection.add(
            documents=knowledge_chunks,
            embeddings=embeddings,
            ids=[f"chunk_{i}" for i in range(len(knowledge_chunks))]
        )
        logger.info(f"Indexed {len(knowledge_chunks)} chunks.")
    except Exception as e:
        logger.error(f"Indexing error: {e}")

async def generate_audio(text: str) -> Optional[str]:
    try:
        resp = client.audio.speech.create(model="tts-1", voice="alloy", input=text)
        return base64.b64encode(resp.content).decode('utf-8')
    except Exception as e:
        logger.error(f"TTS error: {e}"); return None

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, chat_req: ChatRequest):
    start_time = time.time()
    try:
        # Similarity Search
        context = KNOWLEDGE_BASE # Fallback
        if USE_VECTOR_DB and collection:
            q_emb = client.embeddings.create(input=chat_req.message, model="text-embedding-3-small").data[0].embedding
            results = collection.query(query_embeddings=[q_emb], n_results=3)
            context = "\n\n".join(results['documents'][0]) if results['documents'] else KNOWLEDGE_BASE

        system_prompt = f"""You are an AI for Abhijith Sai, a Mathematician and Data Scientist.
        CONTEXT: {context}
        INSTRUCTIONS: Use max 4-5 sentences. Be professional.
        {"VOICE MODE: Be extra concise (2-3 sentences)." if chat_req.is_voice else ""}"""

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": chat_req.message}]
        comp = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.3, max_tokens=400)
        text_resp = comp.choices[0].message.content
        
        audio_b64 = await generate_audio(text_resp) if chat_req.is_voice else None
        
        return ChatResponse(
            response=text_resp,
            session_id=chat_req.session_id,
            processing_time=time.time() - start_time,
            audio=audio_b64
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# --- Static File Serving ---
frontend_path = Path(__file__).parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def read_index(): return FileResponse(frontend_path / "index.html")

@app.get("/{page_name}.html")
async def read_html(page_name: str):
    f = frontend_path / f"{page_name}.html"
    return FileResponse(f) if f.exists() else JSONResponse(status_code=404, content={"detail":"Not found"})

@app.get("/css/{file:path}")
async def css(file: str): return FileResponse(frontend_path / "css" / file)

@app.get("/js/{file:path}")
async def js(file: str): return FileResponse(frontend_path / "js" / file)

@app.get("/images/{file:path}")
async def img(file: str): return FileResponse(frontend_path / "images" / file)

app.start_time = time.time()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860) # Default HF Space port
