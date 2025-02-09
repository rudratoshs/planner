import jwt
import redis
from prisma import Prisma
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import HTTPException, status
from ..config.settings import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
)

# Initialize Prisma DB
db = Prisma()

# Initialize Redis connection
redis_client = redis.StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True
)

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify if password matches the hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


# JWT Token Handling
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generate a short-lived JWT access token"""
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = data.copy()
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generate a long-lived JWT refresh token"""
    expire = datetime.utcnow() + (
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)  # Longer expiration
    )
    to_encode = data.copy()
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str):
    """Decode JWT token and check blacklist"""
    try:
        # Check if the token is blacklisted
        if redis_client.exists(f"blacklist:{token}"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been blacklisted. Please log in again.",
            )

        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )

    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token. Authentication failed.",
        )


def blacklist_token(token: str, expiration: int = None):
    """Blacklist a JWT token in Redis"""
    expiration = expiration or (ACCESS_TOKEN_EXPIRE_MINUTES * 60)  # Default expiration
    redis_client.setex(f"blacklist:{token}", expiration, "blacklisted")


async def expire_inactive_sessions():
    """Expire user sessions that have been inactive for too long"""
    if not db.is_connected():
        await db.connect()

    expiration_time = datetime.utcnow() - timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    await db.user_session.update_many(
        where={"last_active": {"lt": expiration_time}, "logout_at": None},
        data={"logout_at": datetime.utcnow()},
    )
