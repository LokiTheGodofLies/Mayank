from urllib.parse import quote_plus, unquote_plus
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import MONGO_URL, DATABASE_NAME


def format_mongo_url(url: str) -> str:
    """Safely encodes special characters like '@' in the MongoDB password."""
    if not url or "://" not in url or "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    userinfo, host_part = rest.rsplit("@", 1)
    if ":" in userinfo:
        username, password = userinfo.split(":", 1)
        safe_user = quote_plus(unquote_plus(username))
        safe_pass = quote_plus(unquote_plus(password))
        return f"{scheme}://{safe_user}:{safe_pass}@{host_part}"
    return url


# Initialize MongoDB Client and Database
SAFE_MONGO_URL = format_mongo_url(MONGO_URL)
mongo_client = AsyncIOMotorClient(SAFE_MONGO_URL) if SAFE_MONGO_URL else None
db = mongo_client[DATABASE_NAME] if mongo_client is not None else None
