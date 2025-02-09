from prisma import Prisma
from datetime import datetime

db = Prisma()

async def log_audit_event(user_id: str, action: str, details: str, ip_address: str = None, user_agent: str = None):
    """Logs security-related actions to the database"""
    if not db.is_connected():
        await db.connect()

    await db.audit_log.create(
        data={
            "user_id": user_id,
            "action": action,
            "details": details,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow(),
        }
    )