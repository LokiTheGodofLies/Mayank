from datetime import datetime, timezone, timedelta
from database.connection import db

# Indian Standard Time (IST = UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


async def set_config_var(key: str, value: str) -> None:
    """Saves or updates an environment variable override in MongoDB."""
    if db is None:
        return

    now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    collection = db["config_database"]

    await collection.update_one(
        {"key": key},
        {"$set": {"key": key, "value": str(value), "updated_at": now_str}},
        upsert=True,
    )


async def get_all_config_vars() -> dict[str, str]:
    """Fetches all saved environment variable overrides from MongoDB."""
    if db is None:
        return {}

    collection = db["config_database"]
    cursor = collection.find({})
    result: dict[str, str] = {}
    async for doc in cursor:
        if "key" in doc and "value" in doc:
            result[doc["key"]] = str(doc["value"])
    return result


async def delete_config_var(key: str) -> bool:
    """Deletes a saved variable override from MongoDB so it reverts to the Render default."""
    if db is None:
        return False

    collection = db["config_database"]
    res = await collection.delete_one({"key": key})
    return res.deleted_count > 0
  
