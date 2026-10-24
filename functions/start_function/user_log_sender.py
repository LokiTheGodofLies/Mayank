import html
from datetime import datetime, timezone, timedelta

from telebot.async_telebot import AsyncTeleBot
from telebot.types import User

import config.settings as settings

# Indian Standard Time (IST = UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def get_ist_timestamp() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


async def send_user_start_log(bot: AsyncTeleBot, user: User, role: str) -> None:
    """Logs when a user starts the bot."""
    if not getattr(settings, "LOG_GROUP_ID", None):
        return

    try:
        bot_info = await bot.get_me()
        bot_name = html.escape(bot_info.first_name or "Bot")
        bot_link = (
            f'<a href="https://t.me/{bot_info.username}">{bot_name}</a>'
            if getattr(bot_info, "username", None)
            else bot_name
        )

        user_name = html.escape(user.full_name or "Unknown")
        user_username = f"@{user.username}" if user.username else "None"
        user_profile_link = f'<a href="tg://user?id={user.id}">{user_name}</a>'

        log_text = (
            f"<b>#New_User_Start</b>\n\n"
            f"A new user started {bot_link}\n\n"
            f"<b>User Name:</b> {user_name}\n"
            f"<b>Username:</b> {user_username}\n"
            f"<b>Telegram ID:</b> <code>{user.id}</code>\n"
            f"<b>Profile Link:</b> {user_profile_link}\n"
            f"<b>User Role:</b> <code>{role}</code>\n"
            f"<b>Date & Time:</b> <code>{get_ist_timestamp()}</code>"
        )

        kwargs = {
            "chat_id": int(settings.LOG_GROUP_ID),
            "text": log_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if getattr(settings, "USER_LOG_TOPIC_ID", None):
            kwargs["message_thread_id"] = int(settings.USER_LOG_TOPIC_ID)

        await bot.send_message(**kwargs)
    except Exception as e:
        print(f"[user_log_sender] Error sending user start log: {e}")


async def send_user_bot_ban_log(
    bot: AsyncTeleBot,
    user: User | None,
    *,
    reason: str = "Reason not stated",
    banned_by: str | None = None,
) -> None:
    """Logs when a user is banned from using the bot itself."""
    if not getattr(settings, "LOG_GROUP_ID", None):
        return

    try:
        if user:
            user_name = html.escape(user.full_name or "Unknown User")
            user_username = f"@{user.username}" if user.username else "None"
            user_profile = f'<a href="tg://user?id={user.id}">{user_name}</a>'
            user_id = f"<code>{user.id}</code>"
        else:
            user_name = "Unknown"
            user_username = "None"
            user_profile = "Unknown"
            user_id = "<code>Unknown</code>"

        actor = html.escape(banned_by or "Admin")
        log_text = (
            f"<b>#USER_BOT_BANNED</b>\n\n"
            f"<b>• User:</b> {user_profile}\n"
            f"<b>• Username:</b> {user_username}\n"
            f"<b>• Telegram ID:</b> {user_id}\n"
            f"<b>• Banned By:</b> {actor}\n"
            f"<b>• Reason:</b> {html.escape(reason or 'Reason not stated')}\n"
            f"<b>• Time:</b> <code>{get_ist_timestamp()}</code>"
        )

        kwargs = {
            "chat_id": int(settings.LOG_GROUP_ID),
            "text": log_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if getattr(settings, "USER_LOG_TOPIC_ID", None):
            kwargs["message_thread_id"] = int(settings.USER_LOG_TOPIC_ID)

        await bot.send_message(**kwargs)
    except Exception as e:
        print(f"[user_log_sender] Error sending user bot ban log: {e}")
