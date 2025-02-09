from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import auth, users  
from .config.settings import API_V1_PREFIX, PROJECT_NAME, ALLOWED_ORIGINS
from .utils.logger import logger
from .api.middleware.logging_middleware import LoggingMiddleware
from src.db.session import SessionLocal
from .utils.exception_handler import setup_exception_handlers
from prisma import Prisma

db = Prisma()

app = FastAPI(
    title=PROJECT_NAME,
    openapi_url=f"{API_V1_PREFIX}/openapi.json"
)

# Register exception handlers before adding middleware
setup_exception_handlers(app)

#Logging Middleware should be added after exception handlers
app.add_middleware(LoggingMiddleware)

#CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register Routes
app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(users.router, prefix=API_V1_PREFIX)

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}