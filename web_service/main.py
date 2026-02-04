import os
import time
import logging
import aiohttp
import redis
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from utils.monitor import Monitor
from utils.email_utils import send_contact_email

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

monitor = Monitor()
app = FastAPI(title="Portfolio AI Agent", version="1.0.0", docs_url="/api/docs")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
allowed_hosts = os.getenv("ALLOWED_HOSTS", "*").split(",")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
app.add_middleware(GZipMiddleware, minimum_size=1000)

CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://localhost:8001")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None
    is_voice: bool = False

class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    processing_time: float
    audio: Optional[str] = None

class ContactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)

@app.get("/api/health")
async def health_check():
    return {"status": "OK", "uptime": time.time() - app.start_time}

@app.get("/api/stats")
async def get_stats():
    return monitor.get_stats()

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint_proxy(request: Request, chat_request: ChatRequest):
    start_time = time.time()
    monitor.increment_chat_requests("received")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{CHAT_SERVICE_URL}/api/chat",
                json=chat_request.model_dump(exclude_none=True),
                timeout=90
            ) as response:
                if response.status != 200:
                    logger.error(f"Chat service error: {response.status}")
                    response.raise_for_status()

                data = await response.json()
                proc_time = time.time() - start_time
                monitor.increment_chat_requests("success")
                return ChatResponse(
                    response=data.get("response", "No response."),
                    session_id=data.get("session_id"),
                    processing_time=proc_time,
                    audio=data.get("audio")
                )
    except Exception as e:
        monitor.increment_chat_requests("error")
        logger.error(f"Chat proxy error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/contact")
@limiter.limit("5/minute")
async def contact_endpoint(request: Request, contact_request: ContactRequest):
    logger.info(f"Received contact request from {contact_request.email}")
    
    success = send_contact_email(
        name=contact_request.name,
        email=contact_request.email,
        subject=contact_request.subject,
        message=contact_request.message
    )
    
    if success:
        return {"status": "success", "message": "Email sent successfully"}
    else:
        # In a real scenario, you might want to log this or try a backup method
        raise HTTPException(status_code=500, detail="Failed to send email")

# Static Files
frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def read_index():
    return FileResponse(frontend_path / "index.html")

@app.get("/{page_name}.html")
async def read_html(page_name: str):
    file_path = frontend_path / f"{page_name}.html"
    return FileResponse(file_path) if file_path.exists() else JSONResponse(status_code=404, content={"detail": "Not found"})

@app.get("/css/{file_path:path}")
async def serve_css(file_path: str):
    return FileResponse(frontend_path / "css" / file_path)

@app.get("/js/{file_path:path}")
async def serve_js(file_path: str):
    return FileResponse(frontend_path / "js" / file_path)

@app.get("/images/{file_path:path}")
async def serve_images(file_path: str):
    return FileResponse(frontend_path / "images" / file_path)

app.start_time = time.time()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
