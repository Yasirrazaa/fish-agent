from typing import Optional
import os
import time
import hmac
import hashlib
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-should-be-in-env")
API_KEY = os.getenv("API_KEY", "your-api-key-should-be-in-env")

def verify_api_key(api_key: str) -> bool:
    """
    Verify API key using constant time comparison
    """
    if not api_key:
        return False
    return hmac.compare_digest(api_key, API_KEY)

def create_jwt_token(api_key: str) -> str:
    """
    Create a JWT token for authenticated sessions
    """
    expiration = datetime.utcnow() + timedelta(hours=24)
    data = {
        "api_key": api_key,
        "exp": expiration
    }
    return jwt.encode(data, JWT_SECRET, algorithm="HS256")

def decode_jwt_token(token: str) -> dict:
    """
    Decode and verify JWT token
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class AuthHandler:
    def __init__(self):
        self.bearer = HTTPBearer()

    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> str:
        """
        Verify JWT token or API key
        """
        token = credentials.credentials
        
        # First try JWT token
        try:
            payload = decode_jwt_token(token)
            return payload["api_key"]
        except:
            # If not JWT, try direct API key
            if verify_api_key(token):
                return token
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )

# Rate limiting
class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.rate_limits = {
            "default": {"calls": 10, "window": 60},  # 10 calls per minute
            "premium": {"calls": 100, "window": 60}  # 100 calls per minute
        }

    def is_rate_limited(self, api_key: str, tier: str = "default") -> bool:
        """
        Check if request should be rate limited
        Returns True if rate limited
        """
        now = time.time()
        window = self.rate_limits[tier]["window"]
        max_calls = self.rate_limits[tier]["calls"]

        # Initialize or clean old requests
        if api_key not in self.requests:
            self.requests[api_key] = []
        else:
            self.requests[api_key] = [
                req_time for req_time in self.requests[api_key]
                if now - req_time < window
            ]

        if len(self.requests[api_key]) >= max_calls:
            return True

        self.requests[api_key].append(now)
        return False

    def get_remaining_calls(self, api_key: str, tier: str = "default") -> int:
        """
        Get remaining API calls in current window
        """
        now = time.time()
        window = self.rate_limits[tier]["window"]
        max_calls = self.rate_limits[tier]["calls"]

        if api_key not in self.requests:
            return max_calls

        current_calls = len([
            req_time for req_time in self.requests[api_key]
            if now - req_time < window
        ])

        return max(0, max_calls - current_calls)

rate_limiter = RateLimiter()
auth_handler = AuthHandler()

async def authenticate_request(api_key: str, tier: str = "default"):
    """
    Combined authentication and rate limiting
    """
    # Verify API key
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Check rate limit
    if rate_limiter.is_rate_limited(api_key, tier):
        remaining_time = rate_limiter.rate_limits[tier]["window"]
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {remaining_time} seconds",
            headers={"Retry-After": str(remaining_time)}
        )

    return True
