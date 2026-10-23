from datetime import datetime, timezone, timedelta
from database.connection import db
from config.settings import OWNER_IDS, ADMIN_IDS

# Indian Standard Time (IST = UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def get_user_role(user_id: int) -> str:
    """Determines if the user is an owner, admin, or normal_user."""
    if user_id in OWNER_IDS:
        return "owner"
    if user_id in ADMIN_IDS:
        return "admin"
    return "normal_user"


async def save_user(user_id: int, full_name: str, username: str | None) -> dict:
    """Saves or updates a user in the users_database collection."""
    role = get_user_role(user_id)
    now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

    if db is None:
        return {"user_id": user_id, "role": role, "is_new": True}

    collection = db["users_database"]
    existing_user = await collection.find_one({"user_id": user_id})

    if existing_user is None:
        user_data = {
            "user_id": user_id,
            "full_name": full_name,
            "username": f"@{username}" if username else None,
            "role": role,
            "joined_at": now_str,
            "last_active": now_str,
        }
        await collection.insert_one(user_data)
        return {"user_id": user_id, "role": role, "is_new": True}
    else:
        await collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "full_name": full_name,
                    "username": f"@{username}" if username else None,
                    "role": role,
                    "last_active": now_str,
                }
            },
        )
        return {"user_id": user_id, "role": role, "is_new": False}
      
