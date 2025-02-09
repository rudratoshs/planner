from fastapi import HTTPException, status
from prisma import Prisma
from ...utils.security import create_access_token, verify_password
from datetime import timedelta
from ...config.settings import ACCESS_TOKEN_EXPIRE_MINUTES

db = Prisma()


async def authenticate_user(email: str, password: str):
    if not db.is_connected():
        await db.connect()

    db_user = await db.user.find_unique(where={"email": email})

    if not db_user or not verify_password(password, db_user.password_hash):
        return None 

    return db_user

async def record_failed_login(email: str, ip: str):
    """Track failed login attempts"""
    if not db.is_connected():
        await db.connect()

    await db.failed_login_attempt.create(data={"email": email, "ip": ip})