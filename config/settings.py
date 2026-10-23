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
OWNER_IDS = parse_id_list(os.getenv("OWNER_IDS", ""))
ADMIN_IDS = parse_id_list(os.getenv("ADMIN_IDS", ""))

# Log Group & Forum Topic IDs
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "0"))
USER_LOG_TOPIC_ID = int(os.getenv("USER_LOG_TOPIC_ID", "0"))

# Render Web Service Port
PORT = int(os.getenv("PORT", "8080"))
