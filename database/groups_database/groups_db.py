from datetime import datetime, timezone, timedelta
from database.connection import db

# Indian Standard Time (IST = UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


async def save_group(group_id: int, group_name: str, username: str | None) -> bool:
    """Saves or updates a group in the groups_database collection."""
    if db is None:
        return False

    now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    collection = db["groups_database"]
    formatted_username = f"@{username}" if username else None

    existing = await collection.find_one({"group_id": group_id})
    if existing is None:
        await collection.insert_one(
            {
                "group_id": group_id,
                "group_name": group_name,
                "username": formatted_username,
                "added_at": now_str,
                "updated_at": now_str,
            }
        )
        return True
    else:
        await collection.update_one(
            {"group_id": group_id},
            {
                "$set": {
                    "group_name": group_name,
                    "username": formatted_username,
                    "updated_at": now_str,
                }
            },
        )
        return False
      
