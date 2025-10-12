import time
import logging
from prometheus_client import Counter, Gauge, REGISTRY  # Only import what's needed

# Configure logging for this module
logger = logging.getLogger(__name__)

# Define only application-specific custom metrics here.
# Generic request metrics (count, latency) are typically handled by Instrumentator.
CHAT_REQUESTS = Counter('app_chat_requests_total', 'Total chat requests', ['status'])
EMBEDDING_REQUESTS = Counter('app_embedding_requests_total', 'Total embedding requests', ['source'])
KNOWLEDGE_USAGE = Gauge('app_knowledge_chunks_used', 'Number of knowledge chunks used per request')
RESPONSE_TIME_GAUGE = Gauge('app_response_time_seconds', 'Response time in seconds')


class Monitor:
    def __init__(self):
        self.start_time = time.time()
        # Initialize internal counters for cache hits/misses and total requests
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("Monitor initialized.")

    def increment_chat_requests(self, status: str):
        CHAT_REQUESTS.labels(status=status).inc()

    def increment_embedding_requests(self, source: str):
        EMBEDDING_REQUESTS.labels(source=source).inc()

    def set_knowledge_usage(self, count: int):
        KNOWLEDGE_USAGE.set(count)

    def set_response_time(self, seconds: float):
        RESPONSE_TIME_GAUGE.set(seconds)

    def get_uptime(self) -> float:
        return time.time() - self.start_time

    # Methods for cache tracking
    def increment_cache_hit(self):
        self._cache_hits += 1

    def increment_cache_miss(self):
        self._cache_misses += 1

    def get_cache_hits(self) -> int:
        return self._cache_hits

    def get_cache_misses(self) -> int:
        return self._cache_misses

    def get_total_chat_requests(self) -> int:
        # Sum of all chat requests based on Prometheus metric
        # Accessing _value directly is generally for debugging; a robust way involves querying the registry.
        # However, for a simple in-memory monitor, this is acceptable.
        total = 0
        try:
            total += CHAT_REQUESTS.labels(status='success')._value
        except KeyError:
            pass
        try:
            total += CHAT_REQUESTS.labels(status='error')._value
        except KeyError:
            pass
        try:
            total += CHAT_REQUESTS.labels(status='received')._value
        except KeyError:
            pass
        return int(total)

    def get_average_response_time(self) -> float:
        # This would require more sophisticated tracking (e.g., a rolling average).
        # For now, return the last set value or 0 if no requests have been processed.
        return RESPONSE_TIME_GAUGE._value if self.get_total_chat_requests() > 0 else 0.0
