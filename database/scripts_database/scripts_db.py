from datetime import datetime, timezone, timedelta
from database.connection import db
from config.strings import DEFAULT_SCRIPTS

scripts_collection = db["scripts_database"]


def get_ist_time() -> str:
    """Returns current timestamp formatted in Indian Standard Time (IST, UTC+5:30)."""
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_tz).strftime("%Y-%m-%d %I:%M:%S %p IST")


async def init_scripts_db_indexes() -> None:
    """Ensures a unique index on script_key in scripts_database."""
    try:
        await scripts_collection.create_index("script_key", unique=True)
    except Exception as e:
        print(f"[SCRIPTS_DB INDEX ERROR] {e}")


async def get_script_config(script_key: str) -> dict:
    """
    Fetches the configuration for a given script_key from MongoDB.
    If not customized yet, returns the default template from config/strings.py
    with an empty media_pool and empty buttons list.
    """
    default_text = DEFAULT_SCRIPTS.get(script_key, "")
    doc = await scripts_collection.find_one({"script_key": script_key})

    if not doc:
        return {
            "script_key": script_key,
            "text": default_text,
            "is_custom_text": False,
            "parse_mode": "HTML",
            "media_pool": [],
            "buttons": [],
        }

    custom_text = doc.get("custom_text")
    effective_text = custom_text if (custom_text is not None and custom_text != "") else default_text

    return {
        "script_key": script_key,
        "text": effective_text,
        "is_custom_text": bool(custom_text is not None and custom_text != ""),
        "parse_mode": doc.get("parse_mode", "HTML"),
        "media_pool": doc.get("media_pool", []),
        "buttons": doc.get("buttons", []),
        "updated_at": doc.get("updated_at"),
    }


async def update_script_text(script_key: str, new_text: str, parse_mode: str = "HTML") -> bool:
    """Saves custom message text and parse_mode for a script."""
    try:
        await scripts_collection.update_one(
            {"script_key": script_key},
            {
                "$set": {
                    "custom_text": new_text,
                    "parse_mode": parse_mode,
                    "updated_at": get_ist_time(),
                }
            },
            upsert=True,
        )
        return True
    except Exception as e:
        print(f"[SCRIPTS_DB TEXT UPDATE ERROR] {e}")
        return False


async def add_script_media(
    script_key: str,
    file_id: str,
    file_unique_id: str,
    media_type: str,
    duration: int | None = None,
) -> tuple[bool, str]:
    """
    Adds a photo, animation (GIF), or short video (<= 10 seconds) to the script's random media pool.
    Returns (success, message).
    """
    media_type = media_type.lower().strip()
    if media_type not in ("photo", "animation", "video"):
        return False, "Only Photos, GIFs (Animations), and Short Videos (<= 10s) are supported."

    if media_type == "video" and duration is not None and duration > 10:
        return False, f"Video is {duration} seconds long! Please send a video of 10 seconds or less."

    config = await get_script_config(script_key)
    pool = config.get("media_pool", [])

    for item in pool:
        if item.get("file_unique_id") == file_unique_id:
            return False, "This media item is already in the script's media pool."

    new_item = {
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "media_type": media_type,
        "duration": duration,
        "added_at": get_ist_time(),
    }

    try:
        await scripts_collection.update_one(
            {"script_key": script_key},
            {
                "$push": {"media_pool": new_item},
                "$set": {"updated_at": get_ist_time()},
            },
            upsert=True,
        )
        return True, f"Added {media_type.upper()} to {script_key} media pool (Total items: {len(pool) + 1})."
    except Exception as e:
        print(f"[SCRIPTS_DB ADD MEDIA ERROR] {e}")
        return False, "Database error while saving media."


async def remove_script_media_by_index(script_key: str, index: int) -> tuple[bool, str]:
    """Removes a specific media item from the script's media_pool by its 0-based index."""
    config = await get_script_config(script_key)
    pool = config.get("media_pool", [])

    if index < 0 or index >= len(pool):
        return False, "Invalid media item index."

    removed = pool.pop(index)
    try:
        await scripts_collection.update_one(
            {"script_key": script_key},
            {
                "$set": {
                    "media_pool": pool,
                    "updated_at": get_ist_time(),
                }
            },
            upsert=True,
        )
        return True, f"Removed {removed.get('media_type', 'media')} #{index + 1} from pool."
    except Exception as e:
        print(f"[SCRIPTS_DB REMOVE MEDIA ERROR] {e}")
        return False, "Failed to remove media item."


async def clear_script_media(script_key: str) -> bool:
    """Clears all media items from the script's random media pool."""
    try:
        await scripts_collection.update_one(
            {"script_key": script_key},
            {
                "$set": {
                    "media_pool": [],
                    "updated_at": get_ist_time(),
                }
            },
            upsert=True,
        )
        return True
    except Exception as e:
        print(f"[SCRIPTS_DB CLEAR MEDIA ERROR] {e}")
        return False


async def set_script_buttons(script_key: str, button_rows: list[list[dict]]) -> bool:
    """
    Replaces the custom button rows for a script.
    Each button dict in a row has: {"text": str, "type": "url" | "callback", "value": str}
    """
    try:
        await scripts_collection.update_one(
            {"script_key": script_key},
            {
                "$set": {
                    "buttons": button_rows,
                    "updated_at": get_ist_time(),
                }
            },
            upsert=True,
        )
        return True
    except Exception as e:
        print(f"[SCRIPTS_DB SET BUTTONS ERROR] {e}")
        return False


async def add_script_button_row(script_key: str, new_row: list[dict]) -> bool:
    """Appends a new row of custom buttons to a script."""
    try:
        await scripts_collection.update_one(
            {"script_key": script_key},
            {
                "$push": {"buttons": new_row},
                "$set": {"updated_at": get_ist_time()},
            },
            upsert=True,
        )
        return True
    except Exception as e:
        print(f"[SCRIPTS_DB ADD BUTTON ROW ERROR] {e}")
        return False


async def remove_script_button_row(script_key: str, row_index: int) -> tuple[bool, str]:
    """Removes a specific button row by its 0-based index."""
    config = await get_script_config(script_key)
    rows = config.get("buttons", [])

    if row_index < 0 or row_index >= len(rows):
        return False, "Invalid button row number."

    rows.pop(row_index)
    ok = await set_script_buttons(script_key, rows)
    if ok:
        return True, f"Removed button row #{row_index + 1}."
    return False, "Failed to update buttons."


async def clear_script_buttons(script_key: str) -> bool:
    """Clears all custom buttons for a script."""
    return await set_script_buttons(script_key, [])


async def reset_script_to_default(script_key: str) -> bool:
    """Resets a script's text, media pool, and buttons back to factory defaults."""
    try:
        await scripts_collection.delete_one({"script_key": script_key})
        return True
    except Exception as e:
        print(f"[SCRIPTS_DB RESET ERROR] {e}")
        return False
