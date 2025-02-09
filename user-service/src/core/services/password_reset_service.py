import uuid
import secrets
from datetime import datetime, timedelta
from prisma import Prisma
from ...utils.security import hash_password
from ...config.settings import ACCESS_TOKEN_EXPIRE_MINUTES

db = Prisma()

async def generate_password_reset_token(email: str):
    if not db.is_connected():
        await db.connect()

    user = await db.user.find_unique(where={"email": email})
    if not user:
        return None  # User not found

    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    await db.password_reset_token.create(
        data={"user_id": user.id, "token": reset_token, "expires_at": expires_at}
    )
    return reset_token

async def verify_password_reset_token(token: str):
    if not db.is_connected():
        await db.connect()

    reset_token_entry = await db.password_reset_token.find_unique(where={"token": token})
    if not reset_token_entry or reset_token_entry.expires_at < datetime.utcnow():
        return None  # Token is invalid or expired
    return reset_token_entry.user_id

async def reset_password(token: str, new_password: str):
    user_id = await verify_password_reset_token(token)
    if not user_id:
        return False  # Invalid token

    hashed_password = hash_password(new_password)
    await db.user.update(where={"id": user_id}, data={"password_hash": hashed_password})

    # Remove used token from the database
    await db.password_reset_token.delete(where={"token": token})
    return True