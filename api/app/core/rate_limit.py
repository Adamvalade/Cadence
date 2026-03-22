import time
from collections import defaultdict

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60, enabled: bool = True):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.enabled = enabled
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup(self, key: str) -> None:
        now = time.time()
        cutoff = now - self.window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def check(self, request: Request) -> None:
        if not self.enabled:
            return
        ip = request.client.host if request.client else "unknown"
        key = f"{ip}:{request.url.path}"
        self._cleanup(key)
        if len(self._requests[key]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )
        self._requests[key].append(time.time())


from app.core.config import settings

auth_limiter = RateLimiter(max_requests=15, window_seconds=60, enabled=settings.is_production)
