import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()


def parse_id_list(val: str | list | set | tuple | None) -> list[int]:
    """Parses a comma- or whitespace-separated string of IDs into a list of integers."""
    if not val:
        return []
    if isinstance(val, (list, set, tuple)):
        result = []
        for item in val:
            try:
                result.append(int(str(item).strip()))
            except (ValueError, TypeError):
                continue
        return result

    raw_parts = str(val).replace(",", " ").split()
    ids: list[int] = []
    for part in raw_parts:
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            continue
    return ids


def parse_optional_int(val: Any, default: int | None = None) -> int | None:
    """Safely parses an optional integer from an environment variable or config value."""
    if val is None or val == "":
        return default
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return default


# Telegram API & Bot Credentials
API_ID: int | None = parse_optional_int(os.getenv("API_ID"))
API_HASH: str = os.getenv("API_HASH", "").strip()
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

# MongoDB Configuration (supports both MONGO_URL and MONGO_URI from .env.example)
MONGO_URL: str = (os.getenv("MONGO_URL") or os.getenv("MONGO_URI") or "").strip()
MONGO_URI: str = MONGO_URL
DATABASE_NAME: str = (os.getenv("DATABASE_NAME") or "MayankBotDB").strip()

# Role & Access Control Lists
OWNER_IDS: list[int] = parse_id_list(os.getenv("OWNER_IDS") or os.getenv("OWNER_ID", ""))
OWNER_ID: int | None = OWNER_IDS[0] if OWNER_IDS else parse_optional_int(os.getenv("OWNER_ID"))
ADMIN_IDS: list[int] = parse_id_list(os.getenv("ADMIN_IDS", ""))
VOLUNTEER_IDS: list[int] = parse_id_list(os.getenv("VOLUNTEER_IDS", ""))
BANNED_USER_IDS: list[int] = parse_id_list(os.getenv("BANNED_USER_IDS", ""))

# Logging Group & Forum Topic IDs
LOG_GROUP_ID: int | None = parse_optional_int(os.getenv("LOG_GROUP_ID"))
USER_LOG_TOPIC_ID: int | None = parse_optional_int(os.getenv("USER_LOG_TOPIC_ID"))
CHANNEL_LOG_TOPIC_ID: int | None = parse_optional_int(os.getenv("CHANNEL_LOG_TOPIC_ID"))
GROUP_LOG_TOPIC_ID: int | None = parse_optional_int(os.getenv("GROUP_LOG_TOPIC_ID"))
INDEX_LOG_TOPIC_ID: int | None = parse_optional_int(os.getenv("INDEX_LOG_TOPIC_ID"))
ERROR_LOG_TOPIC_ID: int | None = parse_optional_int(os.getenv("ERROR_LOG_TOPIC_ID"))

# Indexing & File Sharing Channels
INDEX_CHANNEL_ID: int | None = parse_optional_int(os.getenv("INDEX_CHANNEL_ID"))
FILE_SHARING_CHANNEL_ID: int | None = parse_optional_int(os.getenv("FILE_SHARING_CHANNEL_ID"))
FILE_AUTO_DELETE_SECONDS: int = parse_optional_int(os.getenv("FILE_AUTO_DELETE_SECONDS"), 600) or 600

# Supported File Extensions
EBOOK_EXTENSIONS: set[str] = {
    ".pdf", ".epub", ".mobi", ".azw3", ".cbz", ".cbr",
    ".djvu", ".txt", ".doc", ".docx", ".rtf", ".fb2",
}
AUDIOBOOK_EXTENSIONS: set[str] = {
    ".mp3", ".m4b", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".wav", ".wma",
}
ALLOWED_EXTENSIONS: set[str] = EBOOK_EXTENSIONS | AUDIOBOOK_EXTENSIONS

# Server & Deployment Settings
PORT: int = parse_optional_int(os.getenv("PORT"), 8080) or 8080
RENDER_DEPLOY_HOOK_URL: str = os.getenv("RENDER_DEPLOY_HOOK_URL", "").strip()

_ID_LIST_KEYS = {"OWNER_IDS", "ADMIN_IDS", "VOLUNTEER_IDS", "BANNED_USER_IDS"}
_INT_KEYS = {
    "API_ID",
    "OWNER_ID",
    "LOG_GROUP_ID",
    "USER_LOG_TOPIC_ID",
    "CHANNEL_LOG_TOPIC_ID",
    "GROUP_LOG_TOPIC_ID",
    "INDEX_LOG_TOPIC_ID",
    "ERROR_LOG_TOPIC_ID",
    "INDEX_CHANNEL_ID",
    "FILE_SHARING_CHANNEL_ID",
    "FILE_AUTO_DELETE_SECONDS",
    "PORT",
}


def apply_config_overrides(overrides: dict[str, Any]) -> None:
    """Applies runtime configuration overrides stored in MongoDB to module globals."""
    if not overrides:
        return

    g = globals()
    for key, raw_val in overrides.items():
        if not key:
            continue
        norm_key = str(key).strip().upper()
        if norm_key in _ID_LIST_KEYS:
            g[norm_key] = parse_id_list(raw_val)
            if norm_key == "OWNER_IDS" and g["OWNER_IDS"]:
                g["OWNER_ID"] = g["OWNER_IDS"][0]
        elif norm_key in _INT_KEYS:
            default_val = g.get(norm_key)
            g[norm_key] = parse_optional_int(raw_val, default=default_val)
        elif norm_key in ("MONGO_URI", "MONGO_URL"):
            val_str = str(raw_val).strip()
            g["MONGO_URL"] = val_str
            g["MONGO_URI"] = val_str
        else:
            g[norm_key] = str(raw_val).strip() if raw_val is not None else ""
