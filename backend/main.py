from fastapi.responses import PlainTextResponse

from backend.imports_file import *
from slowapi import _rate_limit_exceeded_handler

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)
logger.info("Starting Portfolio AI Agent...")

# Initializing Monitor
monitor = Monitor()
app = FastAPI(title="Portfolio AI Agent",
              description="AI powered chat agent for portfolio website with RAG Capabilities",
              version="1.0.0",
              docs_url="/api/docs",
              redoc_url="/api/redoc"
              )
# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://127.0.0.1:3000",
                   "https://your-netlify-site.netlify.app",
                   "https://*.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(","))
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.1")
KNOWLEDGE_BASE_FILE = os.getenv("KNOWLEDGE_BASE_FILE", "knowledge_base.txt")
USE_VECTOR_DB = os.getenv("USE_VECTOR_DB", "false").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes

# Initializing Redis for caching
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis server is connected and running successfully.")
except redis.ConnectionError:
    logger.warning("Redis not available, using in-memory cache")
    redis_client = None

# Initializing the Vector DB using ChromaDB
chroma_client = None
collection = None
if USE_VECTOR_DB:
    try:
        chroma_client = chromadb.Client(Settings(
            persist_directory="./chroma_db",
            anonymized_telemetry=False
        ))
        collection = chroma_client.get_or_create_collection("portfolio_knowledge")
        logger.info("ChromaDB vector database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")

# Initialize sentence transformer for local embeddings (fallback)
local_embedder = None
try:
    local_embedder = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/app/.cache/torch/sentence_transformers')
    logger.info("Local embedding model loaded")
except Exception as e:
    logger.warning(f"Failed to load local embedding model: {e}")

"""# Prometheus metrics
REQUEST_COUNT = Counter('request_count', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency', ['endpoint'])
CHAT_REQUEST_COUNT = Counter('chat_requests_total', 'Total chat requests', ['status'])
EMBEDDING_REQUEST_COUNT = Counter('embedding_requests_total', 'Total embedding requests', ['source'])
"""


# Instrument the app
# Instrumentator().instrument(app).expose(app, endpoint="/api/metrics")


# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User message to process")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation history")


class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    processing_time: float


class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
    uptime: float


class StatsResponse(BaseModel):
    total_chunks: int
    total_requests: int
    cache_hits: int
    cache_misses: int
    average_response_time: float


# Load knowledge base from file
def load_knowledge_base(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            logger.info(f"Loaded knowledge base from {file_path} ({len(content)} characters)")
            return content
    except Exception as e:
        logger.error(f"Error loading knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Failed to load knowledge base")


# Knowledge base - Enhanced with your portfolio data
KNOWLEDGE_BASE = load_knowledge_base(KNOWLEDGE_BASE_FILE)


def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """Split text into manageable chunks with overlap"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_length = 0

    for i, sentence in enumerate(sentences):
        sentence_length = len(sentence)

        if current_length + sentence_length > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            # Keep some overlap for context
            current_chunk = current_chunk[-2:] if len(current_chunk) > 3 else []
            current_length = sum(len(s) for s in current_chunk)

        current_chunk.append(sentence)
        current_length += sentence_length

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


# Chunk the knowledge base
knowledge_chunks = chunk_text(KNOWLEDGE_BASE)
logger.info(f"Knowledge base chunks: {len(knowledge_chunks)}")

# Initialize vector database with knowledge chunks
if USE_VECTOR_DB and collection:
    try:
        # Check if collection is empty
        if collection.count() == 0:
            embeddings = []
            if local_embedder:
                embeddings = local_embedder.encode(knowledge_chunks).tolist()

            collection.add(
                documents=knowledge_chunks,
                embeddings=embeddings if embeddings else None,
                ids=[f"chunk_{i}" for i in range(len(knowledge_chunks))]
            )
            logger.info(f"Added {len(knowledge_chunks)} chunks to vector database")
    except Exception as e:
        logger.error(f"Failed to initialize vector database: {e}")


# Cache functions
def get_cache(key: str) -> Optional[Any]:
    if not redis_client:
        return None
    try:
        cached = redis_client.get(key)
        return json.loads(cached) if cached else None
    except Exception:
        return None


def set_cache(key: str, value: Any, ttl: int = CACHE_TTL):
    if not redis_client:
        return
    try:
        redis_client.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.warning(f"Cache set failed: {e}")


async def generate_embedding(text: str) -> List[float]:
    """Generate text embedding with fallback strategies"""
    # EMBEDDING_REQUEST_COUNT.labels(source='ollama').inc()
    monitor.increment_embedding_requests(source='ollama')

    # Try Ollama first
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{OLLAMA_BASE_URL}/api/embeddings",
                    json={"model": EMBEDDING_MODEL, "prompt": text},
                    timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("embedding", [])
    except Exception as e:
        logger.warning(f"Ollama embedding failed: {e}")

    # Fallback to local model
    monitor.increment_embedding_requests(source='local')
    if local_embedder:
        try:
            embedding = local_embedder.encode([text])[0].tolist()
            return embedding
        except Exception as e:
            logger.error(f"Local embedding failed: {e}")

    # Final fallback: simple TF-IDF like approach
    return [len(text) / 1000.0]  # Simple fallback


async def find_relevant_context(query: str, top_k: int = 3) -> str:
    """Find relevant context using multiple strategies"""
    cache_key = f"context:{hash(query)}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    try:
        if USE_VECTOR_DB and collection:
            # Use vector database search
            query_embedding = await generate_embedding(query)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            relevant_chunks = results['documents'][0] if results['documents'] else []
        else:
            # Use semantic search
            query_embedding = await generate_embedding(query)
            similarities = []

            for chunk in knowledge_chunks:
                chunk_embedding = await generate_embedding(chunk)
                similarity = np.dot(query_embedding, chunk_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                )
                similarities.append((chunk, similarity))

            similarities.sort(key=lambda x: x[1], reverse=True)
            relevant_chunks = [chunk for chunk, score in similarities[:top_k] if score > 0.1]

        if not relevant_chunks:
            relevant_chunks = knowledge_chunks[:2]

        result = "\n\n".join(relevant_chunks)
        set_cache(cache_key, result)
        return result

    except Exception as e:
        logger.error(f"Context search failed: {e}")
        return "\n\n".join(knowledge_chunks[:2])


async def chat_with_ollama(messages: List[dict]) -> str:
    """Send chat request to Ollama with retry logic"""
    for attempt in range(3):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{OLLAMA_BASE_URL}/api/chat",
                        json={
                            "model": CHAT_MODEL,
                            "messages": messages,
                            "stream": False,
                            "options": {"temperature": 0.3, "top_p": 0.9}
                        },
                        timeout=60
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("message", {}).get("content", "No response generated")
                    elif attempt == 2:
                        raise HTTPException(status_code=502, detail="Ollama service unavailable")
        except Exception as e:
            if attempt == 2:
                logger.error(f"Final Ollama attempt failed: {e}")
                raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
            await asyncio.sleep(1 * (attempt + 1))

    return "Sorry, I'm experiencing technical difficulties. Please try again later."


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Portfolio AI Agent API is running"}


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "OK",
        "message": "Service healthy",
        "version": "2.0.0",
        "uptime": time.time() - app.start_time
    }


@app.get("/api/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type="text/plain; version=0.0.4; charset=utf-8")


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    return {
        "total_chunks": len(knowledge_chunks),
        "total_requests": 0,  # Would need tracking
        "cache_hits": 0,  # Would need tracking
        "cache_misses": 0,  # Would need tracking
        "average_response_time": 0.0
    }


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    start_time = time.time()
    monitor.increment_chat_requests("received")
    try:
        context = await find_relevant_context(chat_request.message)

        system_prompt = f"""You are an AI assistant for Abhijith Sai, a Mathematician and Data Scientist.

        ABOUT ABHIJITH:
        {context}

        INSTRUCTIONS:
        - Be professional, friendly, and concise
        - Use ONLY the information provided
        - Admit when you don't know something
        - Keep responses under 3-4 sentences
        - Focus on skills, projects, and experience
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": chat_request.message}
        ]

        response = await chat_with_ollama(messages)
        processing_time = time.time() - start_time

        monitor.increment_chat_requests(status="success")
        monitor.set_response_time(time.time() - start_time)
        return ChatResponse(
            response=response,
            session_id=chat_request.session_id,
            processing_time=processing_time
        )

    except Exception as e:
        processing_time = time.time() - start_time
        monitor.increment_chat_requests(status="error")
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/knowledge/refresh")
async def refresh_knowledge():
    """Force reload of knowledge base"""
    global KNOWLEDGE_BASE, knowledge_chunks
    try:
        KNOWLEDGE_BASE = load_knowledge_base(KNOWLEDGE_BASE_FILE)
        knowledge_chunks = chunk_text(KNOWLEDGE_BASE)

        if USE_VECTOR_DB and collection:
            collection.delete(ids=[f"chunk_{i}" for i in range(collection.count())])
            # Re-add chunks to vector DB

        return {"status": "success", "message": f"Reloaded {len(knowledge_chunks)} chunks"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {e}")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Store startup time
app.start_time = time.time()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        timeout_keep_alive=60
    )
