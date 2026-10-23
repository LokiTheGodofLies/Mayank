import html
from datetime import datetime, timezone, timedelta
from telebot.async_telebot import AsyncTeleBot
from telebot.types import User
from config.settings import LOG_GROUP_ID, USER_LOG_TOPIC_ID

# Indian Standard Time (IST = UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


async def send_user_start_log(bot: AsyncTeleBot, user: User, role: str) -> None:
    """Sends a formatted log message to the User Logs forum topic when a user starts the bot."""
    if not LOG_GROUP_ID:
        return

    try:
        bot_info = await bot.get_me()
        bot_name = html.escape(bot_info.first_name or "Bot")
        bot_link = f'<a href="https://t.me/{bot_info.username}">{bot_name}</a>'

        user_name = html.escape(user.full_name or "Unknown")
        user_username = f"@{user.username}" if user.username else "None"
        user_profile_link = f'<a href="tg://user?id={user.id}">{user_name}</a>'
        now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

        log_text = (
            f"<b>#New_User_Start</b>\n\n"
            f"A new user started {bot_link}\n\n"
            f"<b>User Name:</b> {user_name}\n"
            f"<b>Username:</b> {user_username}\n"
            f"<b>Telegram ID:</b> <code>{user.id}</code>\n"
            f"<b>Profile Link:</b> {user_profile_link}\n"
            f"<b>User Role:</b> <code>{role}</code>\n"
            f"<b>Date & Time:</b> <code>{now_str}</code>"
        )

        kwargs = {
            "chat_id": LOG_GROUP_ID,
            "text": log_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if USER_LOG_TOPIC_ID > 0:
            kwargs["message_thread_id"] = USER_LOG_TOPIC_ID

        await bot.send_message(**kwargs)
    except Exception as e:
        print(f"[user_log_sender] Error sending user start log: {e}")
