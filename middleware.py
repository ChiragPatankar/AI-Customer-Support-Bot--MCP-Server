from fastapi import Request, HTTPException
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import time
from mcp_config import mcp_settings

class RateLimiter:
    def __init__(self, requests_per_period: int, period_in_seconds: int):
        self.requests_per_period = requests_per_period
        self.period_in_seconds = period_in_seconds
        self.requests: Dict[str, list] = defaultdict(list)

    def is_rate_limited(self, client_id: str) -> Tuple[bool, Dict]:
        now = datetime.now()
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < timedelta(seconds=self.period_in_seconds)
        ]
        
        # Check if rate limited
        if len(self.requests[client_id]) >= self.requests_per_period:
            oldest_request = self.requests[client_id][0]
            reset_time = oldest_request + timedelta(seconds=self.period_in_seconds)
            return True, {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded",
                "details": {
                    "reset_time": reset_time.isoformat(),
                    "requests_allowed": self.requests_per_period,
                    "period_seconds": self.period_in_seconds
                }
            }
        
        # Add new request
        self.requests[client_id].append(now)
        return False, {}

# Create rate limiter instance
rate_limiter = RateLimiter(
    requests_per_period=mcp_settings.RATE_LIMIT_REQUESTS,
    period_in_seconds=mcp_settings.RATE_LIMIT_PERIOD
)

async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for non-MCP endpoints
    if not request.url.path.startswith("/mcp/"):
        return await call_next(request)

    # Get client ID from auth header or IP
    client_id = request.headers.get("X-MCP-Auth", request.client.host)
    
    # Check rate limit
    is_limited, error_details = rate_limiter.is_rate_limited(client_id)
    if is_limited:
        return JSONResponse(
            status_code=429,
            content=error_details
        )
    
    return await call_next(request)

async def validate_mcp_request(request: Request, call_next):
    if not request.url.path.startswith("/mcp/"):
        return await call_next(request)

    # Validate MCP version header
    mcp_version = request.headers.get("X-MCP-Version")
    if mcp_version and mcp_version not in ["1.0"]:
        return JSONResponse(
            status_code=400,
            content={
                "code": "UNSUPPORTED_MCP_VERSION",
                "message": f"Unsupported MCP version: {mcp_version}",
                "details": {
                    "supported_versions": ["1.0"]
                }
            }
        )

    return await call_next(request) 