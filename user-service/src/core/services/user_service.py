from prisma.models import user
from ...utils.security import hash_password, verify_password
from prisma import Prisma

db = Prisma()

async def get_user_by_email(email: str):
    if not db.is_connected():  # ✅ Ensure Prisma is connected
        await db.connect()

    return await db.user.find_unique(where={"email": email})


async def create_user(email: str, password: str, full_name: str = None):
    if not db.is_connected():  # ✅ Ensure Prisma is connected
        await db.connect()

    hashed_password = hash_password(password)
    return await db.user.create(
        data={"email": email, "password_hash": hashed_password, "full_name": full_name}
    )
