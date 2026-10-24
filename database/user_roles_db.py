from datetime import datetime
from database.connection import db


async def init_user_roles_indexes() -> None:
    if db is None:
        return

    collection = db["user_roles"]
    await collection.create_index("user_id", unique=True)
    await collection.create_index("role")
    await collection.create_index("updated_at")


async def get_user_role_record(user_id: int) -> dict | None:
    if db is None:
        return None

    return await db["user_roles"].find_one({"user_id": int(user_id)})


async def get_user_role(user_id: int) -> str:
    record = await get_user_role_record(user_id)
    if record and "role" in record:
        return str(record["role"]).lower()

    return "user"


async def set_user_role(user_id: int, role: str) -> None:
    if db is None:
        return

    role = str(role).lower()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    await db["user_roles"].update_one(
        {"user_id": int(user_id)},
        {"$set": {
            "user_id": int(user_id),
            "role": role,
            "updated_at": now,
        }},
        upsert=True,
    )
