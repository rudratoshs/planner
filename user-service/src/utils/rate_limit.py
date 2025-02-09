import redis
from fastapi import HTTPException, status
from ..config.settings import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
)

# Redis Configuration
redis_client = redis.StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True
)

# Rate limit configurations
RATE_LIMITS = {
    "login": {"max_attempts": 5, "window": 60},  # 5 attempts per 60 sec
    "password_reset": {"max_attempts": 3, "window": 3600},  # 3 per hour
    "refresh_token": {"max_attempts": 10, "window": 60},  # 10 per minute
}


def is_rate_limited(action: str, identifier: str):
    """
    Check if the given action (login, password reset) has exceeded rate limits.

    :param action: Action name (e.g., 'login', 'password_reset')
    :param identifier: Unique key (e.g., user's email)
    :return: True if rate limited, False otherwise
    """
    key = f"rate_limit:{action}:{identifier}"
    limit_config = RATE_LIMITS.get(action)

    if not limit_config:
        return False  # No rate limit configured

    attempts = redis_client.get(key)

    if attempts and int(attempts) >= limit_config["max_attempts"]:
        return True  # Block request

    redis_client.incr(key)
    redis_client.expire(key, limit_config["window"])  # Reset count after window
    return False


def reset_rate_limit(action: str, identifier: str):
    """Manually reset the rate limit for a given action and identifier."""
    key = f"rate_limit:{action}:{identifier}"
    redis_client.delete(key)
