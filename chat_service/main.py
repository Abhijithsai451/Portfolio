from slowapi import _rate_limit_exceeded_handler
from sentence_transformers import SentenceTransformer
from utils.imports_file import *
import chromadb
from chromadb.config import Settings
import numpy as np

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)
logger.info("Starting Chat AI Service...")

monitor = Monitor()  # This will only monitor chat service specific metrics

app = FastAPI(title="Portfolio AI Chat Service",
              description="AI powered chat agent for portfolio website with RAG Capabilities",
              version="1.0.0",
              docs_url="/api/docs",
              redoc_url="/api/redoc"
              )

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://127.0.0.1:3000",
                   "https://your-netlify-site.netlify.app",
                   "https://*.netlify.app",
                   os.getenv("CORE_SERVICE_URL", "http://localhost:8000")],  # Allow core service
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
allowed_hosts_list = os.getenv("ALLOWED_HOSTS", "*").split(",")
logger.info(f"Configured ALLOWED_HOSTS for TrustedHostMiddleware: {allowed_hosts_list}")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.1")
KNOWLEDGE_BASE_FILE = os.getenv("KNOWLEDGE_BASE_FILE", "knowledge_base.txt")
USE_VECTOR_DB = os.getenv("USE_VECTOR_DB", "true").lower() == "true"  # Ensure this is true for chat service
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes

# Initializing Redis for caching (can be shared with core service if accessible)
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
        try:
            chroma_client.delete_collection("portfolio_knowledge")
        except Exception:
            pass
        collection = chroma_client.get_or_create_collection("portfolio_knowledge")
        logger.info("ChromaDB vector database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")

# Initialize sentence transformer for local embeddings
local_embedder = None
try:
    local_embedder = SentenceTransformer('all-mpnet-base-v2', cache_folder='./.cache/torch/sentence_transformers')
    logger.info("Local embedding model loaded")
except Exception as e:
    logger.warning(f"Failed to load local embedding model: {e}. Ensure model files are in volume or downloaded.")


# Pydantic models for chat
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User message to process")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation history")


class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    processing_time: float


# Load knowledge base from file
def load_knowledge_base(file_path: str) -> str:
    try:
        # Assuming knowledge_base.txt is in the chat_service directory or its parent
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            logger.info(f"Loaded knowledge base from {file_path} ({len(content)} characters)")
            return content
    except Exception as e:
        logger.error(f"Error loading knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Failed to load knowledge base")


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


# Load and chunk knowledge base on startup
KNOWLEDGE_BASE = load_knowledge_base(KNOWLEDGE_BASE_FILE)
knowledge_chunks = chunk_text(KNOWLEDGE_BASE)
logger.info(f"Knowledge base chunks: {len(knowledge_chunks)}")

# Initialize vector database with knowledge chunks
if USE_VECTOR_DB and collection:
    try:
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
        else:
            logger.info(f"ChromaDB collection already contains {collection.count()} chunks. Skipping initial load.")
    except Exception as e:
        logger.error(f"Failed to initialize vector database with chunks: {e}")


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
            # Use semantic search (fallback if vector DB is not used/failed)
            query_embedding = await generate_embedding(query)
            similarities = []

            for chunk in knowledge_chunks:
                # This approach would be very slow for many chunks without pre-computed embeddings
                chunk_embedding = await generate_embedding(chunk)
                similarity = np.dot(query_embedding, chunk_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                )
                similarities.append((chunk, similarity))

            similarities.sort(key=lambda x: x[1], reverse=True)
            relevant_chunks = [chunk for chunk, score in similarities[:top_k] if score > 0.1]

        if not relevant_chunks:
            # If no relevant chunks found, provide a default from knowledge base
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


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
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
        monitor.set_response_time(processing_time)
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
    """Force reload of knowledge base and re-index vector DB"""
    global KNOWLEDGE_BASE, knowledge_chunks
    try:
        KNOWLEDGE_BASE = load_knowledge_base(KNOWLEDGE_BASE_FILE)
        knowledge_chunks = chunk_text(KNOWLEDGE_BASE)

        if USE_VECTOR_DB and collection:
            # Clear existing data and re-add
            collection.delete(ids=[f"chunk_{i}" for i in range(collection.count())])
            embeddings = []
            if local_embedder:
                embeddings = local_embedder.encode(knowledge_chunks).tolist()
            collection.add(
                documents=knowledge_chunks,
                embeddings=embeddings if embeddings else None,
                ids=[f"chunk_{i}" for i in range(len(knowledge_chunks))]
            )
            logger.info(f"Re-indexed {len(knowledge_chunks)} chunks into vector database")

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
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,  # Chat service will run on a different internal port, e.g., 8001
        log_level="info",
        timeout_keep_alive=60
    )
