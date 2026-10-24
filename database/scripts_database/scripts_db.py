import math
import re
from datetime import datetime, timezone, timedelta

from bson import ObjectId

from database.connection import db

files_collection = db["files_database"] if db is not None else None


def get_ist_time() -> str:
    """Returns current timestamp formatted in Indian Standard Time (IST, UTC+5:30)."""
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_tz).strftime("%Y-%m-%d %I:%M:%S %p IST")


async def init_files_db_indexes() -> None:
    """Creates indexes on file_unique_id, file_type, and file_name for fast lookups."""
    if files_collection is None:
        return
    try:
        await files_collection.create_index("file_unique_id", unique=True)
        await files_collection.create_index("file_type")
        await files_collection.create_index("file_name")
    except Exception as e:
        print(f"[FILES_DB INDEX ERROR] {e}")


async def is_file_already_indexed(file_unique_id: str) -> dict | None:
    """
    Checks if a file with the given file_unique_id already exists in the database.
    Returns the existing document if found, otherwise None.
    """
    if not file_unique_id or files_collection is None:
        return None
    return await files_collection.find_one({"file_unique_id": file_unique_id})


async def update_indexed_file_channel_msg(
    file_unique_id: str,
    db_channel_id: int,
    db_message_id: int,
    new_file_id: str | None = None,
) -> bool:
    """
    Updates the Telegram Index Channel message ID (db_message_id) in MongoDB
    when a previously indexed file was missing/deleted from INDEX_CHANNEL_ID
    and had to be re-forwarded during Dual-Check /index.
    """
    if not file_unique_id or files_collection is None:
        return False

    update_fields: dict = {
        "db_channel_id": int(db_channel_id),
        "db_message_id": int(db_message_id),
        "updated_at": get_ist_time(),
    }
    if new_file_id:
        update_fields["file_id"] = new_file_id

    try:
        await files_collection.update_one(
            {"file_unique_id": file_unique_id},
            {"$set": update_fields},
        )
        return True
    except Exception as e:
        print(f"[FILES_DB UPDATE MSG ERROR] {e}")
        return False


async def save_indexed_file(file_data: dict) -> tuple[bool, dict]:
    """
    Saves an indexed eBook or Audiobook record in MongoDB.
    Returns (is_new_insert, document).
    """
    if files_collection is None:
        return False, {"file_unique_id": file_data.get("file_unique_id"), "file_name": file_data.get("file_name", "Unknown")}

    now_ist = get_ist_time()
    file_unique_id = file_data.get("file_unique_id")

    existing = await is_file_already_indexed(file_unique_id)
    if existing:
        return False, existing

    record = {
        "file_unique_id": file_unique_id,
        "file_id": file_data.get("file_id", ""),
        "file_name": file_data.get("file_name", "Unknown"),
        "file_size": int(file_data.get("file_size") or 0),
        "caption": file_data.get("caption") or "",
        "duration": file_data.get("duration"),
        "file_extension": str(file_data.get("file_extension") or "").lstrip(".").lower(),
        "file_type": str(file_data.get("file_type") or "ebook").lower(),
        "db_channel_id": file_data.get("db_channel_id"),
        "db_message_id": file_data.get("db_message_id"),
        "source_chat_id": file_data.get("source_chat_id"),
        "source_chat_title": file_data.get("source_chat_title") or "Unknown Chat",
        "source_chat_username": file_data.get("source_chat_username"),
        "source_message_id": file_data.get("source_message_id"),
        "topic_id": file_data.get("topic_id"),
        "is_direct_upload": bool(file_data.get("is_direct_upload", False)),
        "indexed_at": now_ist,
    }

    result = await files_collection.insert_one(record)
    record["_id"] = result.inserted_id
    return True, record


async def get_file_by_id(record_id: str) -> dict | None:
    """
    Fetches a single indexed file by its MongoDB _id string or file_unique_id.
    Used when a user clicks a file button in /search results.
    """
    if not record_id or files_collection is None:
        return None
    try:
        if ObjectId.is_valid(record_id):
            doc = await files_collection.find_one({"_id": ObjectId(record_id)})
            if doc:
                return doc
    except Exception:
        pass
    return await files_collection.find_one({"file_unique_id": record_id})


def _build_word_to_word_filter(query: str, file_type: str | None = None, strict_boundaries: bool = True) -> dict:
    """
    Builds a MongoDB filter matching every word from the search query
    in either file_name or caption.
    """
    words = [w.strip() for w in re.split(r"[\s_\-\.]+", query.strip()) if w.strip()]
    and_conditions = []

    for word in words:
        escaped = re.escape(word)
        if strict_boundaries:
            pattern = rf"(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])"
        else:
            pattern = escaped

        regex_obj = {"$regex": pattern, "$options": "i"}
        and_conditions.append(
            {
                "$or": [
                    {"file_name": regex_obj},
                    {"caption": regex_obj},
                ]
            }
        )

    mongo_filter: dict = {}
    if and_conditions:
        mongo_filter["$and"] = and_conditions

    if file_type in ("ebook", "audiobook"):
        mongo_filter["file_type"] = file_type

    return mongo_filter


async def search_indexed_files(
    query: str,
    file_type: str | None = None,
    page: int = 1,
    per_page: int = 10,
) -> tuple[list[dict], int, int]:
    """
    Performs word-to-word search across file_name and caption.
    Returns (results_for_page, total_matching_files, total_pages).
    """
    if not query or not query.strip() or files_collection is None:
        return [], 0, 1

    mongo_filter = _build_word_to_word_filter(query, file_type=file_type, strict_boundaries=True)
    total_count = await files_collection.count_documents(mongo_filter)

    if total_count == 0:
        mongo_filter = _build_word_to_word_filter(query, file_type=file_type, strict_boundaries=False)
        total_count = await files_collection.count_documents(mongo_filter)

    if total_count == 0:
        return [], 0, 1

    total_pages = max(1, math.ceil(total_count / per_page))
    page = max(1, min(page, total_pages))
    skip_count = (page - 1) * per_page

    cursor = (
        files_collection.find(mongo_filter)
        .sort("_id", -1)
        .skip(skip_count)
        .limit(per_page)
    )
    results = await cursor.to_list(length=per_page)
    return results, total_count, total_pages
