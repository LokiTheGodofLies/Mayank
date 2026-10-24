import math
import re
from datetime import datetime, timedelta, timezone

from bson import ObjectId

from config.strings import DEFAULT_SCRIPTS
from database.connection import db

IST = timezone(timedelta(hours=5, minutes=30))


scripts_collection = db["scripts_database"] if db is not None else None


def get_ist_time() -> str:
    """Returns the current timestamp formatted in Indian Standard Time (IST)."""
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_tz).strftime("%Y-%m-%d %H:%M:%S IST")


async def init_scripts_db_indexes() -> None:
    """Creates the required indexes for script customization storage."""
    if db is None:
        return

    collection = db["scripts_database"]
    try:
        await collection.create_index("script_key", unique=True)
    except Exception:
        pass


async def _get_scripts_collection():
    if db is None:
        return None
    return db["scripts_database"]


async def get_script_config(script_key: str) -> dict:
    """Fetches the stored config for a script, falling back to the default template."""
    if not script_key:
        return {}

    collection = await _get_scripts_collection()
    if collection is None:
        return {
            "script_key": script_key,
            "text": DEFAULT_SCRIPTS.get(script_key, ""),
            "media_pool": [],
            "buttons": [],
        }

    doc = await collection.find_one({"script_key": script_key})
    if not doc:
        return {
            "script_key": script_key,
            "text": DEFAULT_SCRIPTS.get(script_key, ""),
            "media_pool": [],
            "buttons": [],
        }

    config = dict(doc)
    config.setdefault("script_key", script_key)
    config.setdefault("text", DEFAULT_SCRIPTS.get(script_key, ""))
    config.setdefault("media_pool", [])
    config.setdefault("buttons", [])
    return config


async def update_script_text(script_key: str, new_text: str, parse_mode: str = "HTML") -> bool:
    """Stores a custom script text value for a given key."""
    if not script_key:
        return False

    collection = await _get_scripts_collection()
    if collection is None:
        return False

    await collection.update_one(
        {"script_key": script_key},
        {
            "$set": {
                "script_key": script_key,
                "text": str(new_text),
                "updated_at": get_ist_time(),
                "parse_mode": parse_mode,
            }
        },
        upsert=True,
    )
    return True


async def add_script_media(
    script_key: str,
    file_id: str,
    file_unique_id: str,
    media_type: str,
    duration: int | None = None,
) -> tuple[bool, str]:
    """Adds a media item to the script media pool."""
    if not script_key or not file_id:
        return False, "Invalid script media payload."

    collection = await _get_scripts_collection()
    if collection is None:
        return False, "Script database is unavailable."

    script = await get_script_config(script_key)
    media_pool = list(script.get("media_pool") or [])
    if not any(item.get("file_unique_id") == file_unique_id for item in media_pool):
        media_pool.append(
            {
                "file_id": file_id,
                "file_unique_id": file_unique_id,
                "media_type": media_type,
                "duration": duration,
            }
        )

    await collection.update_one(
        {"script_key": script_key},
        {
            "$set": {
                "script_key": script_key,
                "media_pool": media_pool,
                "updated_at": get_ist_time(),
            }
        },
        upsert=True,
    )
    return True, f"✅ Added media to <code>{script_key}</code>."


async def clear_script_media(script_key: str) -> bool:
    """Clears the media pool for the script."""
    if not script_key:
        return False

    collection = await _get_scripts_collection()
    if collection is None:
        return False

    await collection.update_one(
        {"script_key": script_key},
        {
            "$set": {
                "script_key": script_key,
                "media_pool": [],
                "updated_at": get_ist_time(),
            }
        },
        upsert=True,
    )
    return True


async def add_script_button_row(script_key: str, button_row: list[dict]) -> bool:
    """Adds one row of inline buttons to the script configuration."""
    if not script_key:
        return False

    collection = await _get_scripts_collection()
    if collection is None:
        return False

    script = await get_script_config(script_key)
    buttons = list(script.get("buttons") or [])
    normalized_row = []
    for button in button_row or []:
        normalized_row.append(
            {
                "text": str(button.get("text") or "Button"),
                "type": str(button.get("type") or "callback"),
                "value": str(button.get("value") or ""),
            }
        )

    buttons.append(normalized_row)
    await collection.update_one(
        {"script_key": script_key},
        {
            "$set": {
                "script_key": script_key,
                "buttons": buttons,
                "updated_at": get_ist_time(),
            }
        },
        upsert=True,
    )
    return True


async def clear_script_buttons(script_key: str) -> bool:
    """Clears all button rows for the script."""
    if not script_key:
        return False

    collection = await _get_scripts_collection()
    if collection is None:
        return False

    await collection.update_one(
        {"script_key": script_key},
        {
            "$set": {
                "script_key": script_key,
                "buttons": [],
                "updated_at": get_ist_time(),
            }
        },
        upsert=True,
    )
    return True


async def reset_script_to_default(script_key: str) -> bool:
    """Resets a script config to the repository defaults."""
    if not script_key:
        return False

    default_text = DEFAULT_SCRIPTS.get(script_key, "")
    collection = await _get_scripts_collection()
    if collection is None:
        return False

    await collection.update_one(
        {"script_key": script_key},
        {
            "$set": {
                "script_key": script_key,
                "text": default_text,
                "media_pool": [],
                "buttons": [],
                "updated_at": get_ist_time(),
            }
        },
        upsert=True,
    )
    return True


__all__ = [
    "get_ist_time",
    "init_scripts_db_indexes",
    "get_script_config",
    "update_script_text",
    "add_script_media",
    "clear_script_media",
    "add_script_button_row",
    "clear_script_buttons",
    "reset_script_to_default",
]
