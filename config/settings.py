import os
from dotenv import load_dotenv

load_dotenv()


def parse_id_list(val: str) -> list[int]:
    """Parses a comma or space separated string of IDs into a list of integers."""
    if not val:
        return []
    ids = []
    for item in val.replace(",", " ").split():
        item = item.strip()
        if item.lstrip("-").isdigit():
            ids.append(int(item))
    return ids


def parse_optional_int(
    val: str | None, default: int | None = None
) -> int | None:
    """Safely parses an environment variable string into an integer or returns default."""
    if val is None or str(val).strip() == "":
        return default
    clean = str(val).strip()
    if clean.lstrip("-").isdigit():
        return int(clean)
    return default


# Telegram API & Bot Credentials
API_ID = parse_optional_int(os.getenv("API_ID"), 0)
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# MongoDB Configuration
MONGO_URL = os.getenv("MONGO_URL", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "MayankBotDB")

# Roles & Permissions
OWNER_IDS: list[int] = parse_id_list(os.getenv("OWNER_IDS", ""))
ADMIN_IDS: list[int] = parse_id_list(os.getenv("ADMIN_IDS", ""))

# Log Group & Forum Topic IDs
LOG_GROUP_ID = parse_optional_int(os.getenv("LOG_GROUP_ID"), None)
USER_LOG_TOPIC_ID = parse_optional_int(os.getenv("USER_LOG_TOPIC_ID"), None)
CHANNEL_LOG_TOPIC_ID = parse_optional_int(os.getenv("CHANNEL_LOG_TOPIC_ID"), None)
GROUP_LOG_TOPIC_ID = parse_optional_int(os.getenv("GROUP_LOG_TOPIC_ID"), None)
INDEX_LOG_TOPIC_ID = parse_optional_int(os.getenv("INDEX_LOG_TOPIC_ID"), None)
ERROR_LOG_TOPIC_ID = parse_optional_int(os.getenv("ERROR_LOG_TOPIC_ID"), None)

# File Indexer & File Sharing Channels
INDEX_CHANNEL_ID = parse_optional_int(os.getenv("INDEX_CHANNEL_ID"), None)
FILE_SHARING_CHANNEL_ID = parse_optional_int(
    os.getenv("FILE_SHARING_CHANNEL_ID"), None
)
FILE_AUTO_DELETE_SECONDS = parse_optional_int(
    os.getenv("FILE_AUTO_DELETE_SECONDS"), 300
)

# Supported Book & Audiobook Formats (.zip included in Audiobooks)
EBOOK_EXTENSIONS = {"epub", "pdf", "azw3", "kfx"}
AUDIOBOOK_EXTENSIONS = {"mp3", "m4b", "aax", "zip"}
ALLOWED_EXTENSIONS = EBOOK_EXTENSIONS | AUDIOBOOK_EXTENSIONS

# Web Server & Deployment
PORT = parse_optional_int(os.getenv("PORT"), 8080)
RENDER_DEPLOY_HOOK_URL = os.getenv("RENDER_DEPLOY_HOOK_URL", "")


def apply_config_overrides(overrides: dict) -> None:
    """
    Applies dynamic configuration overrides stored in MongoDB (via /setvar)
    to both os.environ and module-level variables at runtime.
    """
    global API_ID, API_HASH, BOT_TOKEN, MONGO_URL, DATABASE_NAME
    global LOG_GROUP_ID, USER_LOG_TOPIC_ID, CHANNEL_LOG_TOPIC_ID, GROUP_LOG_TOPIC_ID
    global INDEX_LOG_TOPIC_ID, ERROR_LOG_TOPIC_ID
    global INDEX_CHANNEL_ID, FILE_SHARING_CHANNEL_ID, FILE_AUTO_DELETE_SECONDS
    global PORT, RENDER_DEPLOY_HOOK_URL

    if not overrides:
        return

    for key, value in overrides.items():
        os.environ[str(key)] = str(value)

    API_ID = parse_optional_int(os.getenv("API_ID"), API_ID)
    API_HASH = os.getenv("API_HASH", API_HASH)
    BOT_TOKEN = os.getenv("BOT_TOKEN", BOT_TOKEN)
    MONGO_URL = os.getenv("MONGO_URL", MONGO_URL)
    DATABASE_NAME = os.getenv("DATABASE_NAME", DATABASE_NAME)

    # Update role lists in-place so imported references see changes immediately
    OWNER_IDS.clear()
    OWNER_IDS.extend(parse_id_list(os.getenv("OWNER_IDS", "")))

    ADMIN_IDS.clear()
    ADMIN_IDS.extend(parse_id_list(os.getenv("ADMIN_IDS", "")))

    LOG_GROUP_ID = parse_optional_int(os.getenv("LOG_GROUP_ID"), None)
    USER_LOG_TOPIC_ID = parse_optional_int(os.getenv("USER_LOG_TOPIC_ID"), None)
    CHANNEL_LOG_TOPIC_ID = parse_optional_int(
        os.getenv("CHANNEL_LOG_TOPIC_ID"), None
    )
    GROUP_LOG_TOPIC_ID = parse_optional_int(os.getenv("GROUP_LOG_TOPIC_ID"), None)
    INDEX_LOG_TOPIC_ID = parse_optional_int(os.getenv("INDEX_LOG_TOPIC_ID"), None)
    ERROR_LOG_TOPIC_ID = parse_optional_int(os.getenv("ERROR_LOG_TOPIC_ID"), None)

    INDEX_CHANNEL_ID = parse_optional_int(os.getenv("INDEX_CHANNEL_ID"), None)
    FILE_SHARING_CHANNEL_ID = parse_optional_int(
        os.getenv("FILE_SHARING_CHANNEL_ID"), None
    )
    FILE_AUTO_DELETE_SECONDS = parse_optional_int(
        os.getenv("FILE_AUTO_DELETE_SECONDS"), 300
    )

    PORT = parse_optional_int(os.getenv("PORT"), 8080)
    RENDER_DEPLOY_HOOK_URL = os.getenv(
        "RENDER_DEPLOY_HOOK_URL", RENDER_DEPLOY_HOOK_URL
    )
