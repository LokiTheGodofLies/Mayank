import config.settings as settings


def is_owner(user_id: int) -> bool:
    """True only for bot owners."""
    owner_ids = getattr(settings, "OWNER_IDS", []) or []
    return int(user_id) in {int(uid) for uid in owner_ids}


def is_admin(user_id: int) -> bool:
    """True for bot admins and owners."""
    admin_ids = getattr(settings, "ADMIN_IDS", []) or []
    return int(user_id) in {int(uid) for uid in admin_ids}


def is_admin_or_owner(user_id: int) -> bool:
    """True for both admins and owners."""
    return is_admin(user_id) or is_owner(user_id)


async def require_admin_or_owner(bot, message) -> bool:
    """Guard for admin commands. Returns False with a standard reply if blocked."""
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
    """Guard for owner-only commands. Returns False with a standard reply if blocked."""
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
    "is_admin_or_owner",
    "require_admin_or_owner",
    "require_owner",
]
