from functools import wraps
from typing import Any, Callable

import config.settings as settings
from database.ban_db import is_entity_banned
from database.user_roles_db import get_user_role


class _DualBool(int):
    """
    Boolean-like integer that works both synchronously (`if is_admin_or_owner(uid):`)
    and asynchronously (`if await is_admin_or_owner(uid):`).
    """

    def __new__(cls, val: bool, async_resolver: Callable[[], Any] | None = None):
        instance = super().__new__(cls, 1 if val else 0)
        instance._async_resolver = async_resolver
        return instance

    def __bool__(self) -> bool:
        return bool(int(self))

    def __await__(self):
        async def _resolve() -> bool:
            if bool(int(self)):
                return True
            if self._async_resolver is not None:
                try:
                    return bool(await self._async_resolver())
                except Exception:
                    return bool(int(self))
            return bool(int(self))

        return _resolve().__await__()

    def __repr__(self) -> str:
        return "True" if bool(int(self)) else "False"


def is_owner(user_id: int | None) -> _DualBool:
    """Checks if the user ID is configured as a bot owner."""
    if not user_id:
        return _DualBool(False)
    uid = int(user_id)
    owner_ids = set(getattr(settings, "OWNER_IDS", []) or [])
    single_owner = getattr(settings, "OWNER_ID", None)
    if single_owner:
        owner_ids.add(int(single_owner))

    sync_match = uid in owner_ids

    async def _check_db() -> bool:
        role = await get_user_role(uid)
        return role == "owner"

    return _DualBool(sync_match, _check_db)


def is_admin(user_id: int | None) -> _DualBool:
    """Checks if the user ID is configured as an admin (or owner)."""
    if not user_id:
        return _DualBool(False)
    uid = int(user_id)
    admin_ids = set(getattr(settings, "ADMIN_IDS", []) or [])
    sync_match = bool(is_owner(uid)) or (uid in admin_ids)

    async def _check_db() -> bool:
        role = await get_user_role(uid)
        return role in ("owner", "admin")

    return _DualBool(sync_match, _check_db)


def is_volunteer(user_id: int | None) -> _DualBool:
    """Checks if the user ID is configured as a volunteer, admin, or owner."""
    if not user_id:
        return _DualBool(False)
    uid = int(user_id)
    volunteer_ids = set(getattr(settings, "VOLUNTEER_IDS", []) or [])
    sync_match = bool(is_admin(uid)) or (uid in volunteer_ids)

    async def _check_db() -> bool:
        role = await get_user_role(uid)
        return role in ("owner", "admin", "volunteer")

    return _DualBool(sync_match, _check_db)


def is_banned(user_id: int | None) -> _DualBool:
    """Checks if the user ID is in BANNED_USER_IDS or banned in MongoDB."""
    if not user_id:
        return _DualBool(False)
    uid = int(user_id)
    if bool(is_owner(uid)):
        return _DualBool(False)
    banned_ids = set(getattr(settings, "BANNED_USER_IDS", []) or [])
    sync_match = uid in banned_ids

    async def _check_db() -> bool:
        return await is_entity_banned("user", uid)

    return _DualBool(sync_match, _check_db)


def is_admin_or_owner(user_id: int | None) -> _DualBool:
    """Checks if the user is either an admin or an owner (works both sync and awaited)."""
    return is_admin(user_id)


def is_privileged_user(user_id: int | None) -> _DualBool:
    """Checks if the user is an owner, admin, or volunteer."""
    return is_volunteer(user_id)


async def get_effective_role(user_id: int | None) -> str:
    """Resolves the user's highest effective role from settings and MongoDB."""
    if not user_id:
        return "user"
    uid = int(user_id)
    if bool(is_owner(uid)):
        return "owner"
    if uid in set(getattr(settings, "ADMIN_IDS", []) or []):
        return "admin"
    if uid in set(getattr(settings, "VOLUNTEER_IDS", []) or []):
        return "volunteer"

    try:
        db_role = await get_user_role(uid)
        if db_role in ("owner", "admin", "volunteer"):
            return db_role
    except Exception:
        pass
    return "user"


async def check_user_access(user_id: int | None) -> tuple[bool, str]:
    """Validates whether the user is allowed to use the bot."""
    if not user_id:
        return False, "Unable to verify user identity."
    if await is_banned(user_id):
        return False, "🚫 You are banned from using this bot."
    return True, "ok"


def _extract_user_id(target: Any) -> int | None:
    """Extracts a Telegram user ID from a Message, CallbackQuery, or int."""
    if isinstance(target, int):
        return target
    from_user = getattr(target, "from_user", None)
    if from_user is not None:
        return getattr(from_user, "id", None)
    return None


def require_admin_or_owner(*args: Any, **kwargs: Any) -> Any:
    """
    Supports both:
    1. Decorator usage:
       @bot.message_handler(commands=["editscript"])
       @require_admin_or_owner
       async def handler(message): ...
    2. Direct coroutine call:
       if not await require_admin_or_owner(bot, message): return
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @wraps(func)
        async def _decorator_wrapper(*f_args: Any, **f_kwargs: Any) -> Any:
            target = f_args[-1] if f_args else None
            uid = _extract_user_id(target)
            if not uid or not await is_admin_or_owner(uid):
                bot_Instance = f_args[0] if len(f_args) > 1 else None
                if bot_Instance and hasattr(bot_Instance, "reply_to") and hasattr(target, "chat"):
                    try:
                        await bot_Instance.reply_to(target, "❌ Access denied. Admin or Owner privileges required.")
                    except Exception:
                        pass
                return None
            return await func(*f_args, **f_kwargs)

        return _decorator_wrapper

    async def _direct_check() -> bool:
        bot = args[0] if len(args) >= 1 else kwargs.get("bot")
        target = args[1] if len(args) >= 2 else kwargs.get("message") or kwargs.get("call")
        uid = _extract_user_id(target)
        if uid and await is_admin_or_owner(uid):
            return True
        if bot is not None and target is not None:
            try:
                if hasattr(target, "data") and hasattr(bot, "answer_callback_query"):
                    await bot.answer_callback_query(target.id, "❌ Access denied.", show_alert=True)
                elif hasattr(bot, "reply_to"):
                    await bot.reply_to(target, "❌ Access denied. Admin or Owner privileges required.")
            except Exception:
                pass
        return False

    return _direct_check()


def require_owner(*args: Any, **kwargs: Any) -> Any:
    """
    Supports both:
    1. Decorator usage:
       @require_owner
       async def handler(message): ...
    2. Direct coroutine call:
       if not await require_owner(bot, message): return
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @wraps(func)
        async def _decorator_wrapper(*f_args: Any, **f_kwargs: Any) -> Any:
            target = f_args[-1] if f_args else None
            uid = _extract_user_id(target)
            if not uid or not await is_owner(uid):
                bot_instance = f_args[0] if len(f_args) > 1 else None
                if bot_instance and hasattr(bot_instance, "reply_to") and hasattr(target, "chat"):
                    try:
                        await bot_instance.reply_to(target, "❌ Access denied. Owner privileges required.")
                    except Exception:
                        pass
                return None
            return await func(*f_args, **f_kwargs)

        return _decorator_wrapper

    async def _direct_check() -> bool:
        bot = args[0] if len(args) >= 1 else kwargs.get("bot")
        target = args[1] if len(args) >= 2 else kwargs.get("message") or kwargs.get("call")
        uid = _extract_user_id(target)
        if uid and await is_owner(uid):
            return True
        if bot is not None and target is not None:
            try:
                if hasattr(target, "data") and hasattr(bot, "answer_callback_query"):
                    await bot.answer_callback_query(target.id, "❌ Access denied. Owner only.", show_alert=True)
                elif hasattr(bot, "reply_to"):
                    await bot.reply_to(target, "❌ Access denied. Owner privileges required.")
            except Exception:
                pass
        return False

    return _direct_check()


__all__ = [
    "is_owner",
    "is_admin",
    "is_volunteer",
    "is_banned",
    "is_admin_or_owner",
    "is_privileged_user",
    "get_effective_role",
    "check_user_access",
    "require_admin_or_owner",
    "require_owner",
]
