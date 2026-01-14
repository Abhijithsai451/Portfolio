from slowapi import _rate_limit_exceeded_handler

from utils.imports_file import *

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s -  %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info("Starting Core API Service...")

# Initializing Monitor
monitor = Monitor()
app = FastAPI(title="Portfolio AI Agent (Core)",
              description="Core API for Portfolio Website",
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
                   "https://your-netlify-site.netlify.app",
                   "https://*.netlify.app",
                   "*"], # Allow all origins for dev/testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
allowed_hosts_list = os.getenv("ALLOWED_HOSTS", "*").split(",")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts_list)  # Use the variable directly
logger.info(f"Configured ALLOWED_HOSTS for TrustedHostMiddleware: {allowed_hosts_list}")
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes

CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://localhost:8001")

# Initializing Redis for caching (can be shared with chat service if accessible)
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis server is connected and running successfully.")
except redis.ConnectionError:
    logger.warning("Redis not available, using in-memory cache")
    redis_client = None

# Prometheus metrics (Core service specific)
REQUEST_COUNT = Counter('core_request_count', 'Total Core API requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('core_request_latency_seconds', 'Core Request latency', ['endpoint'])
CORE_CHAT_PROXY_COUNT = Counter('core_chat_proxy_requests_total', 'Total chat requests proxied by core', ['status'])


# Pydantic models (redefined here or import from a shared module if needed by both)
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User message to process")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation history")
    is_voice: bool = Field(False, description="Whether the request is from voice mode")


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
    total_chunks: int = 0  # Not applicable to core, or fetched from chat service
    total_requests: int
    cache_hits: int
    cache_misses: int
    average_response_time: float


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Portfolio AI Agent Core API is running"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "OK",
        "message": "Core Service healthy",
        "version": "1.0.0",
        "uptime": time.time() - app.start_time
    }


@app.get("/api/metrics")
async def metrics():
    # This will expose core service metrics.
    # To get chat service metrics, you'd need to fetch them from the chat service directly.
    return PlainTextResponse(generate_latest(), media_type="text/plain; version=0.0.4; charset=utf-8")


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    # This example will only provide core service stats.
    # For chat-specific stats, you'd need to make a request to the chat service.
    return {
        "total_chunks": 0,
        "total_requests": monitor._chat_requests.get("received", 0),
        "cache_hits": 0,  # Implement Redis cache hit/miss tracking if needed
        "cache_misses": 0,
        "average_response_time": monitor.get_stats()["avg_response_time"]
    }


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint_proxy(request: Request, chat_request: ChatRequest):
    start_time = time.time()
    CORE_CHAT_PROXY_COUNT.labels(status="received").inc()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{CHAT_SERVICE_URL}/api/chat",
                    json=chat_request.model_dump(exclude_none=True),  # Exclude None to avoid potential validation issues
                    timeout=90
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Chat service returned status {response.status}: {error_text}")
                    response.raise_for_status()

                chat_response_data = await response.json()
                processing_time = time.time() - start_time
                CORE_CHAT_PROXY_COUNT.labels(status="success").inc()
                return ChatResponse(
                    response=chat_response_data.get("response", "No response from AI service."),
                    session_id=chat_response_data.get("session_id"),
                    processing_time=processing_time
                )
    except aiohttp.ClientResponseError as e:
        processing_time = time.time() - start_time
        CORE_CHAT_PROXY_COUNT.labels(status="error").inc()
        logger.error(f"Failed to communicate with chat service: {e.status}, message='{e.message}'")
        raise HTTPException(status_code=503, detail="AI chat service is unavailable")
    except Exception as e:
        processing_time = time.time() - start_time
        CORE_CHAT_PROXY_COUNT.labels(status="error").inc()
        logger.error(f"Error processing chat request through proxy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


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
        port=8000,
        log_level="info",
        timeout_keep_alive=60
    )
