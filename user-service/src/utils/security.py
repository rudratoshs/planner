import jwt
from prisma import Prisma
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
from ..config.settings import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
import redis
db = Prisma()

# Connect to Redis
redis_client = redis.StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True
)

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# JWT Token Handling
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str):
    try:
        # Check if the token is blacklisted in Redis
        if redis_client.get(token):
            return None

        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        return None
    except PyJWTError:
        return None


def blacklist_token(token: str, expiration: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60):
    """Store token in Redis blacklist"""
    redis_client.setex(token, expiration, "blacklisted")


def create_refresh_token(data: dict, expires_delta: timedelta = None):
    """Generate a new refresh token (longer expiration)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


async def expire_inactive_sessions():
    """Expire sessions that have been inactive for too long."""
    if not db.is_connected():
        await db.connect()

    expiration_time = datetime.utcnow() - timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    await db.user_session.update_many(
        where={"last_active": {"lt": expiration_time}, "logout_at": None},
        data={"logout_at": datetime.utcnow()},
    )
