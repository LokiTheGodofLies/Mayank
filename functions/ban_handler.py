import html

from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import config.settings as settings
from database.ban_db import ban_entity
from functions.permissions import is_admin_or_owner, is_banned


def _detect_entity_type(target_id: int) -> str:
    value = int(target_id)
    if value > 0:
        return "user"
    return "group" if value < 0 else "user"


async def send_ban_log(bot: AsyncTeleBot, entity_type: str, entity_id: int | str, reason: str, banned_by: str) -> None:
    log_group_id = getattr(settings, "LOG_GROUP_ID", None)
    if not log_group_id:
        return

    topic_id = getattr(settings, "USER_LOG_TOPIC_ID", None)
    if entity_type == "group":
        topic_id = getattr(settings, "GROUP_LOG_TOPIC_ID", None)
    elif entity_type == "channel":
        topic_id = getattr(settings, "CHANNEL_LOG_TOPIC_ID", None)

    log_text = (
        f"<b>🚫 Ban Log</b>\n\n"
        f"<b>Type:</b> {html.escape(entity_type.title())}\n"
        f"<b>ID:</b> <code>{entity_id}</code>\n"
        f"<b>Reason:</b> {html.escape(reason)}\n"
        f"<b>Banned By:</b> {html.escape(banned_by)}\n"
    )

    try:
        await bot.send_message(
            chat_id=int(log_group_id),
            text=log_text,
            parse_mode="HTML",
            message_thread_id=int(topic_id) if topic_id else None,
        )
    except Exception:
        pass


async def ensure_user_is_allowed(bot: AsyncTeleBot, message):
    if not message or not getattr(message, "from_user", None):
        return True

    user_id = message.from_user.id
    if is_banned(user_id) or await is_entity_banned("user", user_id):
        await bot.reply_to(
            message,
            "🚫 Access denied. You are banned from using this bot.",
            parse_mode="HTML",
        )
        return False
    return True


async def ensure_chat_is_allowed(bot: AsyncTeleBot, chat_id: int, chat_title: str = "", message=None):
    from database.ban_db import is_entity_banned

    if await is_entity_banned("group", chat_id) or await is_entity_banned("channel", chat_id):
        support_url = getattr(settings, "SUPPORT_CHAT_URL", None) or "https://t.me/your_support_chat"
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("💬 Support", url=support_url))

        if message:
            await bot.reply_to(
                message,
                "🚫 This group/channel is banned.\nContact support for more information.",
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        return False
    return True


def register_ban_handler(bot: AsyncTeleBot) -> None:
    @bot.message_handler(commands=["ban"])
    async def handle_ban_command(message):
        if not message.from_user:
            return

        if not is_admin_or_owner(message.from_user.id):
            await bot.reply_to(
                message,
                "🚫 You are not authorised.\nOnly admins and owners can ban users, groups, or channels.",
                parse_mode="HTML",
            )
            return

        parts = (message.text or "").split()
        if len(parts) < 2:
            await bot.reply_to(
                message,
                "Usage: /ban <user_id|group_id|channel_id> [reason]\nExample: /ban 123456789 spam\nExample: /ban -1001234567890 spam",
                parse_mode="HTML",
            )
            return

        raw_target = parts[1]
        try:
            target_id = int(raw_target)
        except ValueError:
            await bot.reply_to(
                message,
                "Invalid ID. Use a numeric Telegram ID.",
                parse_mode="HTML",
            )
            return

        entity_type = _detect_entity_type(target_id)
        reason = " ".join(parts[2:]) if len(parts) > 2 else ""
        if not reason.strip():
            reason = "Reason not stated"

        ban_result = await ban_entity(
            entity_type=entity_type,
            entity_id=target_id,
            reason=reason,
            banned_by=f"{message.from_user.first_name or 'Admin'} ({message.from_user.id})",
        )

        if ban_result.get("status") == "already_banned":
            await bot.reply_to(
                message,
                f"🚫 {entity_type.title()} {target_id} is already banned.",
                parse_mode="HTML",
            )
            return

        if ban_result.get("status") == "updated":
            await bot.reply_to(
                message,
                f"✅ Ban reason updated for {entity_type.title()} {target_id}.\nReason: {html.escape(reason)}",
                parse_mode="HTML",
            )
            await send_ban_log(
                bot,
                entity_type,
                target_id,
                reason,
                f"{message.from_user.first_name or 'Admin'} ({message.from_user.id})",
            )
            return

        await bot.reply_to(
            message,
            f"✅ {entity_type.title()} {target_id} has been banned.\nReason: {html.escape(reason)}",
            parse_mode="HTML",
        )
        await send_ban_log(
            bot,
            entity_type,
            target_id,
            reason,
            f"{message.from_user.first_name or 'Admin'} ({message.from_user.id})",
        )


__all__ = [
    "register_ban_handler",
    "send_ban_log",
    "ensure_user_is_allowed",
    "ensure_chat_is_allowed",
]
