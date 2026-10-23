from datetime import datetime, timezone, timedelta
from database.connection import db

# Indian Standard Time (IST = UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


async def save_group(
    group_id: int,
    group_name: str,
    username: str | None,
    invite_link: str | None = None,
    status: str = "active",
) -> dict:
    """Saves or updates a group in the groups_database collection and returns the stored record."""
    now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    formatted_username = f"@{username}" if username else None

    if db is None:
        return {
            "group_id": group_id,
            "group_name": group_name,
            "username": formatted_username,
            "invite_link": invite_link,
            "status": status,
        }

    collection = db["groups_database"]
    existing = await collection.find_one({"group_id": group_id})

    # Keep the previously saved invite link if a new one isn't available (e.g., when removed)
    final_invite_link = invite_link or (existing.get("invite_link") if existing else None)

    if existing is None:
        record = {
            "group_id": group_id,
            "group_name": group_name,
            "username": formatted_username,
            "invite_link": final_invite_link,
            "status": status,
            "added_at": now_str,
            "updated_at": now_str,
        }
        await collection.insert_one(record)
        return record
    else:
        update_fields = {
            "group_name": group_name,
            "username": formatted_username,
            "invite_link": final_invite_link,
            "status": status,
            "updated_at": now_str,
        }
        await collection.update_one({"group_id": group_id}, {"$set": update_fields})
        existing.update(update_fields)
        return existing
