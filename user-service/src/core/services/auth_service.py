from fastapi import HTTPException, status
from prisma import Prisma
from ...utils.security import create_access_token, verify_password
from datetime import timedelta
from ...config.settings import ACCESS_TOKEN_EXPIRE_MINUTES

db = Prisma()


async def authenticate_user(email: str, password: str):
    if not db.is_connected():  # ✅ Ensure Prisma is connected
        await db.connect()

    db_user = await db.user.find_unique(where={"email": email})

    if not db_user or not verify_password(password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return token
