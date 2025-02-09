from .environment import env

# Database URL
DATABASE_URL = f"postgresql://{env.POSTGRES_USER}:{env.POSTGRES_PASSWORD}@{env.POSTGRES_HOST}:{env.POSTGRES_PORT}/{env.POSTGRES_DB}"

# Redis URL
REDIS_URL = f"redis://{':' + env.REDIS_PASSWORD + '@' if env.REDIS_PASSWORD else ''}{env.REDIS_HOST}:{env.REDIS_PORT}/0"

# API Settings
API_V1_PREFIX = "/api/v1"
PROJECT_NAME = "User Service"

# CORS Settings
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Frontend local
    "http://localhost:8000",  # Backend local
]

# Cache Settings
CACHE_TTL = 3600  # 1 hour

# ✅ **JWT Settings (Fix)**
JWT_SECRET_KEY = env.JWT_SECRET_KEY
JWT_ALGORITHM = env.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = env.ACCESS_TOKEN_EXPIRE_MINUTES
REDIS_HOST = env.REDIS_HOST
REDIS_PORT = env.REDIS_PORT
REDIS_PASSWORD = env.REDIS_PASSWORD
ACCESS_TOKEN_EXPIRE_MINUTES = env.ACCESS_TOKEN_EXPIRE_MINUTES