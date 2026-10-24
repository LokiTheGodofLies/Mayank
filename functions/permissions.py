import config.settings as settings
from database.user_roles_db import get_user_role as get_db_role


def is_owner(user_id: int) -> bool:
    """True only for bot owners."""
    owner_ids = getattr(settings, "OWNER_IDS", []) or []
    return int(user_id) in {int(uid) for uid in owner_ids}


def is_admin(user_id: int) -> bool:
    """True for bot admins and owners."""
    admin_ids = getattr(settings, "ADMIN_IDS", []) or []
    return int(user_id) in {int(uid) for uid in admin_ids}


def is_volunteer(user_id: int) -> bool:
    """True for volunteers."""
    volunteer_ids = getattr(settings, "VOLUNTEER_IDS", []) or []
    return int(user_id) in {int(uid) for uid in volunteer_ids}


def is_banned(user_id: int) -> bool:
    """True when the user is globally banned."""
    banned_ids = getattr(settings, "BANNED_USER_IDS", []) or []
    return int(user_id) in {int(uid) for uid in banned_ids}


def is_admin_or_owner(user_id: int) -> bool:
    """True for both admins and owners."""
    return is_admin(user_id) or is_owner(user_id)


def is_volunteer_or_admin_or_owner(user_id: int) -> bool:
    """True for volunteers, admins, and owners."""
    return is_volunteer(user_id) or is_admin_or_owner(user_id)


async def get_user_role(user_id: int) -> str:
    """Returns the effective role for a user, preferring DB role if present."""
    db_role = await get_db_role(int(user_id))
    if db_role in {"owner", "admin", "volunteer", "user"}:
        return db_role

    if is_owner(user_id):
        return "owner"
    if is_admin(user_id):
        return "admin"
    if is_volunteer(user_id):
        return "volunteer"
    return "user"


def get_search_limit(user_id: int) -> int:
    """Fallback static limit for non-DB checks."""
    return 10


def get_request_limit(user_id: int) -> int:
    """Fallback static limit for non-DB checks."""
    return 10


async def require_admin_or_owner(bot, message) -> bool:
    """Guard for admin commands."""
    if not message or not getattr(message, "from_user", None):
        return False

    user_id = message.from_user.id
    if not is_admin_or_owner(user_id):
        await bot.reply_to(
            message,
            "🚫 You are not authorised.\nOnly admins and owners can access this command.",
            parse_mode="HTML",
        )
        return False
    return True


async def require_owner(bot, message) -> bool:
    """Guard for owner-only commands."""
    if not message or not getattr(message, "from_user", None):
        return False

    user_id = message.from_user.id
    if not is_owner(user_id):
        await bot.reply_to(
            message,
            "🚫 You are not authorised.\nOnly owners can access this command.",
            parse_mode="HTML",
        )
        return False
    return True


__all__ = [
    "is_owner",
    "is_admin",
    "is_volunteer",
    "is_banned",
    "is_admin_or_owner",
    "is_volunteer_or_admin_or_owner",
    "get_user_role",
    "get_search_limit",
    "get_request_limit",
    "require_admin_or_owner",
    "require_owner",
]
