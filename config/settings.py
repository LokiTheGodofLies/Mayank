import os
from dotenv import load_dotenv

load_dotenv()


def parse_id_list(env_value: str) -> list[int]:
    """Converts a space- or comma-separated string of IDs into a list of integers."""
    if not env_value:
        return []
    cleaned = env_value.replace(",", " ").split()
    return [int(x) for x in cleaned if x.lstrip("-").isdigit()]


# Telegram Credentials
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# MongoDB Connection
MONGO_URL = os.getenv("MONGO_URL", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "telegram_bot_db")

# User Roles
OWNER_IDS: list[int] = parse_id_list(os.getenv("OWNER_IDS", ""))
ADMIN_IDS: list[int] = parse_id_list(os.getenv("ADMIN_IDS", ""))

# Log Group & Forum Topic IDs
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "0"))
USER_LOG_TOPIC_ID = int(os.getenv("USER_LOG_TOPIC_ID", "0"))
CHANNEL_LOG_TOPIC_ID = int(os.getenv("CHANNEL_LOG_TOPIC_ID", "0"))
GROUP_LOG_TOPIC_ID = int(os.getenv("GROUP_LOG_TOPIC_ID", "0"))

# Render Web Service Port & Deploy Hook
PORT = int(os.getenv("PORT", "8080"))
RENDER_DEPLOY_HOOK_URL = os.getenv("RENDER_DEPLOY_HOOK_URL", "")


def apply_config_overrides(overrides: dict[str, str]) -> None:
    """Applies dynamic variable overrides from MongoDB into os.environ and live settings."""
    global API_ID, API_HASH, BOT_TOKEN, MONGO_URL, DATABASE_NAME
    global LOG_GROUP_ID, USER_LOG_TOPIC_ID, CHANNEL_LOG_TOPIC_ID, GROUP_LOG_TOPIC_ID
    global PORT, RENDER_DEPLOY_HOOK_URL

    for k, v in overrides.items():
        os.environ[k] = str(v)

    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    MONGO_URL = os.getenv("MONGO_URL", "")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "telegram_bot_db")

    # Update role lists in-place so all imported modules see changes immediately
    OWNER_IDS.clear()
    OWNER_IDS.extend(parse_id_list(os.getenv("OWNER_IDS", "")))

    ADMIN_IDS.clear()
    ADMIN_IDS.extend(parse_id_list(os.getenv("ADMIN_IDS", "")))

    LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "0"))
    USER_LOG_TOPIC_ID = int(os.getenv("USER_LOG_TOPIC_ID", "0"))
    CHANNEL_LOG_TOPIC_ID = int(os.getenv("CHANNEL_LOG_TOPIC_ID", "0"))
    GROUP_LOG_TOPIC_ID = int(os.getenv("GROUP_LOG_TOPIC_ID", "0"))
    PORT = int(os.getenv("PORT", "8080"))
    RENDER_DEPLOY_HOOK_URL = os.getenv("RENDER_DEPLOY_HOOK_URL", "")
