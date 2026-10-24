import re
from datetime import datetime, timezone, timedelta
from database.connection import db

# Indian Standard Time (IST = UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def format_file_size(size_bytes: int | None) -> str:
    """Formats raw bytes into human-readable KB / MB / GB."""
    if not size_bytes or size_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_idx = 0
    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024.0
        unit_idx += 1
    return f"{size:.2f} {units[unit_idx]}"


def format_duration(seconds: int | None) -> str:
    """Formats audio duration in seconds into HH:MM:SS or MM:SS."""
    if not seconds or seconds <= 0:
        return "N/A"
    hrs, rem = divmod(int(seconds), 3600)
    mins, secs = divmod(rem, 60)
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def extract_search_tokens(*texts: str | None) -> list[str]:
    """Splits filenames, titles, authors, and captions into lowercase searchable words."""
    combined = " ".join(t for t in texts if t)
    words = re.findall(r"[a-zA-Z0-9]+", combined.lower())
    return list(dict.fromkeys(words))


async def init_files_db_indexes() -> None:
    """Creates indexes on file_unique_id and search_words for fast lookups."""
    if db is None:
        return
    try:
        collection = db["files_database"]
        await collection.create_index("file_unique_id", unique=True)
        await collection.create_index("search_words")
        await collection.create_index("file_name")
    except Exception as e:
        print(f"[FILES_DB INDEX WARNING] {e}")


async def get_file_by_unique_id(file_unique_id: str) -> dict | None:
    """Fetches a stored file record by its permanent Telegram file_unique_id."""
    if db is None or not file_unique_id:
        return None
    return await db["files_database"].find_one({"file_unique_id": file_unique_id})


async def save_indexed_file(record: dict) -> tuple[bool, dict]:
    """
    Saves or updates an indexed file in files_database using file_unique_id.
    Returns (is_newly_inserted, stored_record).
    """
    now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    file_unique_id = record.get("file_unique_id") or record.get("file_id")
    record["file_unique_id"] = file_unique_id

    file_size = record.get("file_size", 0)
    duration = record.get("duration")
    record["file_size_str"] = record.get("file_size_str") or format_file_size(file_size)
    record["duration_str"] = record.get("duration_str") or format_duration(duration)

    book_meta = record.get("book_meta") or {}
    record["search_words"] = extract_search_tokens(
        record.get("file_name"),
        record.get("caption"),
        book_meta.get("book_title"),
        book_meta.get("book_author"),
    )
    record["updated_at"] = now_str

    if db is None:
        return True, record

    collection = db["files_database"]
    existing = await collection.find_one({"file_unique_id": file_unique_id})

    if existing is None:
        record["indexed_at"] = now_str
        await collection.insert_one(record)
        return True, record
    else:
        await collection.update_one(
            {"file_unique_id": file_unique_id},
            {"$set": record},
        )
        existing.update(record)
        return False, existing


def _build_word_to_word_filter(query: str) -> dict:
    """Builds a safe, escaped word-by-word MongoDB query filter."""
    clean_words = [w.strip() for w in re.split(r"[\s_\.\-]+", query.strip()) if w.strip()]
    if not clean_words:
        return {}

    and_conditions = []
    for word in clean_words:
        safe_regex = {"$regex": re.escape(word), "$options": "i"}
        and_conditions.append(
            {
                "$or": [
                    {"file_name": safe_regex},
                    {"caption": safe_regex},
                    {"book_meta.book_title": safe_regex},
                    {"book_meta.book_author": safe_regex},
                ]
            }
        )
    return {"$and": and_conditions}


async def search_files(query: str, limit: int = 10, skip: int = 0) -> tuple[list[dict], int]:
    """
    Searches files_database by keyword across file_name, caption, book_title, and book_author.
    Returns (list_of_matching_docs, total_count).
    """
    if db is None or not query or not query.strip():
        return [], 0

    try:
        collection = db["files_database"]
        mongo_filter = _build_word_to_word_filter(query)
        if not mongo_filter:
            return [], 0

        total = await collection.count_documents(mongo_filter)
        cursor = (
            collection.find(mongo_filter)
            .sort("_id", -1)
            .skip(skip)
            .limit(limit)
        )
        results = await cursor.to_list(length=limit)
        return results, total
    except Exception as e:
        print(f"[FILES_DB SEARCH ERROR] {e}")
        return [], 0


async def get_total_files_count() -> int:
    """Returns the total number of indexed files in MongoDB."""
    if db is None:
        return 0
    try:
        return await db["files_database"].count_documents({})
    except Exception as e:
        print(f"[FILES_DB COUNT ERROR] {e}")
        return 0
