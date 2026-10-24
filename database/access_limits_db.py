from datetime import datetime
from database.connection import db


def today_key() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


async def init_access_limit_indexes() -> None:
    if db is None:
        return

    collection = db["user_daily_usage"]
    await collection.create_index("user_id")
    await collection.create_index("date")
    await collection.create_index([("user_id", 1), ("date", 1)], unique=True)


async def get_usage_today(user_id: int) -> dict:
    if db is None:
        return {"search_count": 0, "request_count": 0}

    doc = await db["user_daily_usage"].find_one({
        "user_id": int(user_id),
        "date": today_key(),
    })
    if not doc:
        return {"search_count": 0, "request_count": 0}
    return doc


async def increment_usage(user_id: int, action: str) -> tuple[bool, int]:
    if db is None:
        return True, 0

    from functions.permissions import get_user_role

    role = await get_user_role(int(user_id))
    if role in ("admin", "owner"):
        return True, 10**9

    limit = 20 if role == "volunteer" else 10
    current = (await get_usage_today(user_id)).get(
        "search_count" if action == "search" else "request_count",
        0,
    )

    if current >= limit:
        return False, current

    await db["user_daily_usage"].update_one(
        {"user_id": int(user_id), "date": today_key()},
        {"$setOnInsert": {"user_id": int(user_id), "date": today_key()}},
        upsert=True,
    )

    await db["user_daily_usage"].update_one(
        {"user_id": int(user_id), "date": today_key()},
        {"$inc": {("search_count" if action == "search" else "request_count"): 1}},
    )

    return True, current + 1
