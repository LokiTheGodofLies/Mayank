import html
from datetime import datetime, timezone, timedelta

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Chat, User

import config.settings as settings

IST = timezone(timedelta(hours=5, minutes=30))


def get_ist_timestamp() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


async def send_chat_status_log(
    bot: AsyncTeleBot,
    chat: Chat,
    action_user: User | None,
    action: str,
    invite_link: str | None = None,
) -> None:
    """Sends a log when the bot is added/removed from a group or channel."""
    if not getattr(settings, "LOG_GROUP_ID", None):
        return

    try:
        bot_info = await bot.get_me()
        bot_name = html.escape(bot_info.first_name or "Bot")
        bot_link = f'<a href="https://t.me/{bot_info.username}">{bot_name}</a>' if bot_info.username else bot_name

        is_channel = chat.type == "channel"
        label = "Channel" if is_channel else "Group"
        topic_id = getattr(settings, "CHANNEL_LOG_TOPIC_ID", None) if is_channel else getattr(settings, "GROUP_LOG_TOPIC_ID", None)

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

        now_str = get_ist_timestamp()

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
            "chat_id": int(settings.LOG_GROUP_ID),
            "text": log_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if topic_id:
            kwargs["message_thread_id"] = int(topic_id)

        await bot.send_message(**kwargs)
    except Exception as e:
        print(f"[chat_log_sender] Error sending {chat.type} log: {e}")


async def send_user_action_log(
    bot: AsyncTeleBot,
    user: User | None,
    action: str,
    *,
    chat: Chat | None = None,
    reason: str | None = None,
) -> None:
    """Sends a log for user start, ban, kick, unban, etc."""
    if not getattr(settings, "LOG_GROUP_ID", None):
        return

    topic_id = getattr(settings, "USER_LOG_TOPIC_ID", None)

    if user:
        user_name = html.escape(user.full_name or "Unknown User")
        user_username = f"@{user.username}" if user.username else "<i>None</i>"
        user_id = f"<code>{user.id}</code>"
        user_profile_link = f'<a href="tg://user?id={user.id}">{user_name}</a>'
    else:
        user_name = "Unknown"
        user_username = "<i>Unknown</i>"
        user_id = "<code>Unknown</code>"
        user_profile_link = "Unknown"

    if chat:
        chat_title = html.escape(chat.title or "Unknown Chat")
        chat_id = f"<code>{chat.id}</code>"
        chat_type = chat.type
        if chat.username:
            chat_link_display = f'<a href="https://t.me/{chat.username}">Public Link</a>'
        else:
            chat_link_display = "<i>Private / No Username</i>"
    else:
        chat_title = "N/A"
        chat_id = "<code>N/A</code>"
        chat_type = "N/A"
        chat_link_display = "<i>N/A</i>"

    action_tag = {
        "started_bot": "#USER_STARTED_BOT",
        "banned": "#USER_BANNED",
        "kicked": "#USER_KICKED",
        "left": "#USER_LEFT_CHAT",
        "unbanned": "#USER_UNBANNED",
    }.get(action, "#USER_ACTION")

    text = (
        f"{action_tag}\n\n"
        f"<b>• Action:</b> <code>{html.escape(action)}</code>\n"
        f"<b>• User:</b> {user_profile_link}\n"
        f"<b>• Username:</b> {user_username}\n"
        f"<b>• User ID:</b> {user_id}\n"
        f"<b>• Chat:</b> {chat_title} ({chat_type})\n"
        f"<b>• Chat ID:</b> {chat_id}\n"
        f"<b>• Chat Link:</b> {chat_link_display}\n"
        f"<b>• Reason:</b> {html.escape(reason or 'N/A')}\n"
        f"<b>• Time:</b> <code>{get_ist_timestamp()}</code>"
    )

    send_kwargs = {
        "chat_id": int(settings.LOG_GROUP_ID),
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if topic_id:
        send_kwargs["message_thread_id"] = int(topic_id)

    try:
        await bot.send_message(**send_kwargs)
    except Exception as e:
        print(f"[USER_LOG_SENDER ERROR] {e}")
