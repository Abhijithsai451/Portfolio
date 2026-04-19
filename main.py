import logging
import os
import time
from typing import Optional, List

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from langchain_core.messages import HumanMessage

from utils.monitor import Monitor
from chat_service.agents.graph import portfolio_graph

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
monitor = Monitor()

app = FastAPI(title="Portfolio AI Agent Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None
    is_voice: bool = False

class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    processing_time: float
    audio: Optional[str] = None

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    start = time.time()
    logger.info(f"Incoming Chat Request: session_id={chat_request.session_id}, is_voice={chat_request.is_voice}")
    monitor.increment_chat_requests("received")
    
    try:
        # Initial State
        initial_state = {
            "messages": [HumanMessage(content=chat_request.message)],
            "input_type": "voice" if chat_request.is_voice else "text",
            "session_id": chat_request.session_id,
            "is_skill_query": False,
            "context": None,
            "final_response": None,
            "audio": None
        }
        
        # Invoke Graph
        logger.info("Invoking Portfolio Agent Graph...")
        final_state = await portfolio_graph.ainvoke(initial_state)
        logger.info("Graph invocation complete.")
        
        proc_time = time.time() - start
        monitor.increment_chat_requests("success")
        logger.info(f"Request processed successfully in {proc_time:.2f}s")
        
        return ChatResponse(
            response=final_state.get("final_response", "I'm sorry, I couldn't process that."),
            session_id=chat_request.session_id,
            processing_time=proc_time,
            audio=final_state.get("audio")
        )
        
    except Exception as e:
        logger.error(f"Chat Error: {e}")
        monitor.increment_chat_requests("error")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8001)
