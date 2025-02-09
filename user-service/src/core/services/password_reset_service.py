import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from prisma import Prisma
import pytz
from ...utils.security import hash_password
from ...utils.email import send_email
from ...config.settings import ACCESS_TOKEN_EXPIRE_MINUTES
import logging

db = Prisma()

def hash_reset_token(token: str) -> str:
    """ Hashes the password reset token before storing it """
    return hashlib.sha256(token.encode()).hexdigest()

async def generate_password_reset_token(email: str):
    if not db.is_connected():
        await db.connect()

    user = await db.user.find_unique(where={"email": email})
    if not user:
        return None  # User not found

    raw_token = secrets.token_urlsafe(32)  # Generate raw token
    hashed_token = hash_reset_token(raw_token)  # Hash before storing
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    await db.password_reset_token.create(
        data={"user_id": user.id, "token": hashed_token, "expires_at": expires_at}
    )

    # Send email with the reset link
    reset_link = f"http://localhost:8000/api/v1/auth/reset-password?token={raw_token}"
    email_body = f"""
    <h1>Password Reset Request</h1>
    <p>Click the link below to reset your password:</p>
    <a href="{reset_link}">Reset Password</a>
    <p>If you did not request this, please ignore this email.</p>
    """
    send_email(email, "Password Reset Request", email_body)

    return True  # Do not return the raw token to API response

async def verify_password_reset_token(token: str):
    """Check if a hashed reset token exists in the database"""
    if not db.is_connected():
        await db.connect()

    hashed_token = hash_reset_token(token)  # Hash before lookup
    reset_token_entry = await db.password_reset_token.find_unique(where={"token": hashed_token})

    if not reset_token_entry:
        logging.warning("Token not found in database")
        return None  # Token not found

    # Convert `expires_at` to a timezone-naive datetime
    expires_at_naive = reset_token_entry.expires_at.replace(tzinfo=None)

    if expires_at_naive < datetime.utcnow():
        logging.warning("Token is expired")
        return None  # Token has expired

    return reset_token_entry.user_id

async def reset_password(token: str, new_password: str):
    """Reset password after verifying the hashed reset token"""
    hashed_token = hash_reset_token(token)  # Hash before lookup

    user_id = await verify_password_reset_token(token)  # Verify using hashed token
    if not user_id:
        return False  # Invalid or expired token

    hashed_password = hash_password(new_password)

    # Update the password in the database
    await db.user.update(where={"id": user_id}, data={"password_hash": hashed_password})

    # Remove the used token from the database (hashed version)
    await db.password_reset_token.delete(where={"token": hashed_token})

    return True