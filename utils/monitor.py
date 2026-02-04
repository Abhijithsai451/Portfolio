import time

class Monitor:
    def __init__(self):
        self.start_time = time.time()
        self._stats = {"received": 0, "success": 0, "error": 0}
        self._last_time = 0.0

    def increment_chat_requests(self, status: str):
        if status in self._stats: self._stats[status] += 1

    def set_response_time(self, seconds: float):
        self._last_time = seconds

    def get_stats(self) -> dict:
        return {
            "uptime": time.time() - self.start_time,
            "total_requests": sum(self._stats.values()),
            "chat_stats": self._stats,
            "avg_response_time": self._last_time
        }
