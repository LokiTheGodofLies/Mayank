import html
from datetime import datetime, timezone, timedelta
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Chat, User
from config.settings import LOG_GROUP_ID, CHANNEL_LOG_TOPIC_ID, GROUP_LOG_TOPIC_ID

# Indian Standard Time (IST = UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


async def send_chat_status_log(
    bot: AsyncTeleBot,
    chat: Chat,
    action_user: User | None,
    action: str,
    invite_link: str | None = None,
) -> None:
    """
    Sends a formatted log message when the bot is added to or removed from a channel or group.
    action: 'added' or 'removed'
    """
    if not LOG_GROUP_ID:
        return

    try:
        bot_info = await bot.get_me()
        bot_name = html.escape(bot_info.first_name or "Bot")
        bot_link = f'<a href="https://t.me/{bot_info.username}">{bot_name}</a>'

        is_channel = chat.type == "channel"
        label = "Channel" if is_channel else "Group"
        topic_id = CHANNEL_LOG_TOPIC_ID if is_channel else GROUP_LOG_TOPIC_ID

        chat_title = html.escape(chat.title or f"Unnamed {label}")
        chat_username = f"@{chat.username}" if chat.username else "Private"

        if chat.username:
            chat_link_display = f'<a href="https://t.me/{chat.username}">Public Link</a>'
        elif invite_link:
            chat_link_display = f'<a href="{html.escape(invite_link)}">Private Invite Link</a>'
        else:
            chat_link_display = "Not available (No admin invite permission)"

        if action_user:
            user_name = html.escape(action_user.full_name or "Unknown")
            user_username = f"@{action_user.username}" if action_user.username else "None"
            user_id_str = f"<code>{action_user.id}</code>"
            user_profile_link = f'<a href="tg://user?id={action_user.id}">{user_name}</a>'
        else:
            user_name = "Unknown"
            user_username = "None"
            user_id_str = "<code>Unknown</code>"
            user_profile_link = "Unknown"

        now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

        if action == "added":
            header = f"<b>#Bot_Added_To_{label}</b>"
            summary_line = f"{bot_link} was <b>added</b> to {label}: <b>{chat_title}</b>"
        else:
            header = f"<b>#Bot_Removed_From_{label}</b>"
            summary_line = f"{bot_link} was <b>removed</b> from {label}: <b>{chat_title}</b>"

        log_text = (
            f"{header}\n\n"
            f"{summary_line}\n\n"
            f"<b>{label} Name:</b> {chat_title}\n"
            f"<b>{label} ID:</b> <code>{chat.id}</code>\n"
            f"<b>{label} Username:</b> {chat_username}\n"
            f"<b>{label} Link:</b> {chat_link_display}\n\n"
            f"<b>Action By User:</b>\n"
            f"• <b>Name:</b> {user_name}\n"
            f"• <b>Username:</b> {user_username}\n"
            f"• <b>User ID:</b> {user_id_str}\n"
            f"• <b>Profile Link:</b> {user_profile_link}\n\n"
            f"<b>Date & Time:</b> <code>{now_str}</code>"
        )

        kwargs = {
            "chat_id": LOG_GROUP_ID,
            "text": log_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if topic_id > 0:
            kwargs["message_thread_id"] = topic_id

        await bot.send_message(**kwargs)
    except Exception as e:
        print(f"[chat_log_sender] Error sending {chat.type} log: {e}")
