import html
from datetime import datetime, timezone, timedelta
from telebot.async_telebot import AsyncTeleBot
import config.settings as settings


def get_ist_timestamp() -> str:
    """Returns current timestamp formatted in Indian Standard Time (IST, UTC+5:30)."""
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_tz).strftime("%Y-%m-%d %I:%M:%S %p IST")


def format_file_size(size_in_bytes: int) -> str:
    """Converts byte count into a human-readable KB / MB / GB string."""
    if not size_in_bytes or size_in_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_in_bytes)
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"


def format_duration(seconds: int | None) -> str:
    """Formats audio duration in seconds into HH:MM:SS or MM:SS."""
    if not seconds or seconds <= 0:
        return "N/A"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def build_message_link(chat_id: int | str, message_id: int | str, chat_username: str | None = None) -> str | None:
    """
    Builds a direct Telegram link to a message inside a public or private channel/supergroup.
    - Public chat: https://t.me/<username>/<message_id>
    - Private supergroup/channel (-100xxxxxxxxxx): https://t.me/c/<internal_id>/<message_id>
    """
    if not message_id or message_id == "N/A":
        return None

    if chat_username:
        clean_username = chat_username.lstrip("@")
        return f"https://t.me/{clean_username}/{message_id}"

    chat_id_str = str(chat_id)
    if chat_id_str.startswith("-100"):
        internal_id = chat_id_str[4:]
        return f"https://t.me/c/{internal_id}/{message_id}"

    return None


async def resolve_chat_invite_link(
    bot: AsyncTeleBot,
    chat_id: int | str,
    chat_username: str | None = None,
    provided_invite_link: str | None = None,
) -> str | None:
    """
    Returns a clickable URL for the source chat:
    1. If public username exists -> https://t.me/<username>
    2. If an invite link is already provided -> provided_invite_link
    3. If private chat and bot has invite permissions -> fetches chat.invite_link or exports one
    """
    if chat_username:
        return f"https://t.me/{chat_username.lstrip('@')}"

    if provided_invite_link:
        return provided_invite_link

    if not chat_id or chat_id == "N/A":
        return None

    try:
        chat_obj = await bot.get_chat(chat_id)
        if getattr(chat_obj, "username", None):
            return f"https://t.me/{chat_obj.username}"
        if getattr(chat_obj, "invite_link", None):
            return chat_obj.invite_link
        return await bot.export_chat_invite_link(chat_id)
    except Exception:
        return None


async def send_index_log(bot: AsyncTeleBot, file_data: dict) -> None:
    """
    Sends an HTML-formatted log message to LOG_GROUP_ID under INDEX_LOG_TOPIC_ID
    whenever a new eBook or Audiobook is indexed into the database.
    """
    log_group_id = getattr(settings, "LOG_GROUP_ID", None)
    if not log_group_id:
        return

    index_topic_id = getattr(settings, "INDEX_LOG_TOPIC_ID", None)

    file_type_raw = str(file_data.get("file_type", "ebook")).lower()
    if file_type_raw == "audiobook":
        type_header = "🎧 <b>#NEW_AUDIOBOOK_INDEXED</b>"
        type_label = "Audiobook 🎧"
    else:
        type_header = "📚 <b>#NEW_EBOOK_INDEXED</b>"
        type_label = "eBook 📚"

    file_name = html.escape(str(file_data.get("file_name") or "Unknown"))
    file_ext = html.escape(str(file_data.get("file_extension") or "").lstrip(".").lower())
    file_size_str = format_file_size(file_data.get("file_size", 0))
    duration_str = format_duration(file_data.get("duration"))
    file_id = html.escape(str(file_data.get("file_id") or "N/A"))

    raw_caption = (file_data.get("caption") or "").strip()
    if raw_caption:
        trimmed_caption = raw_caption[:250] + ("..." if len(raw_caption) > 250 else "")
        caption_str = html.escape(trimmed_caption)
    else:
        caption_str = "<i>No caption</i>"

    # Source Chat Title with embedded public or private invite link
    source_title_escaped = html.escape(str(file_data.get("source_chat_title") or "Unknown Chat"))
    source_id = file_data.get("source_chat_id", "N/A")
    source_username = file_data.get("source_chat_username")
    provided_invite_link = file_data.get("source_invite_link")
    is_direct = file_data.get("is_direct_upload", False)

    chat_url = await resolve_chat_invite_link(
        bot=bot,
        chat_id=source_id,
        chat_username=source_username,
        provided_invite_link=provided_invite_link,
    )

    if chat_url:
        linked_source_title = f'<a href="{html.escape(chat_url)}">{source_title_escaped}</a>'
    else:
        linked_source_title = source_title_escaped

    if is_direct:
        source_display = f"{linked_source_title} (<i>Direct Upload to Index Channel</i>)"
    elif source_username:
        source_display = f"{linked_source_title} (@{html.escape(source_username.lstrip('@'))})"
    else:
        source_display = f"{linked_source_title} (<i>Private</i>)"

    # Indexed Database Message Link
    db_channel_id = file_data.get("db_channel_id") or getattr(settings, "INDEX_CHANNEL_ID", None)
    db_channel_username = file_data.get("db_channel_username")
    db_message_id = file_data.get("db_message_id", "N/A")

    db_msg_url = build_message_link(
        chat_id=db_channel_id,
        message_id=db_message_id,
        chat_username=db_channel_username,
    )
    if db_msg_url:
        db_msg_display = f'<a href="{html.escape(db_msg_url)}">View Indexed File (Msg #{db_message_id})</a>'
    else:
        db_msg_display = f"<code>{db_message_id}</code>"

    # Sender details if directly added to the Index Database Channel
    sender_block = ""
    if is_direct:
        sender_id = file_data.get("sender_id")
        sender_name = html.escape(str(file_data.get("sender_name") or file_data.get("author_signature") or "Unknown Admin"))
        sender_username = file_data.get("sender_username")

        if sender_id:
            user_link = f"tg://user?id={sender_id}"
            linked_user_name = f'<a href="{user_link}">{sender_name}</a>'
            linked_user_id = f'<a href="{user_link}"><code>{sender_id}</code></a>'
        else:
            linked_user_name = sender_name
            linked_user_id = "<i>Hidden (Anonymous Channel Post)</i>"

        if sender_username:
            clean_u = html.escape(sender_username.lstrip("@"))
            username_display = f"@{clean_u}"
        else:
            username_display = "<i>None</i>"

        sender_block = (
            f"<b>• Sender Name:</b> {linked_user_name}\n"
            f"<b>• Sender Username:</b> {username_display}\n"
            f"<b>• Sender User ID:</b> {linked_user_id}\n"
        )

    timestamp = get_ist_timestamp()

    log_text = (
        f"{type_header}\n\n"
        f"<b>• File Name:</b> <code>{file_name}</code>\n"
        f"<b>• File Type:</b> {type_label}\n"
        f"<b>• Extension:</b> <code>.{file_ext}</code>\n"
        f"<b>• File Size:</b> <code>{file_size_str}</code>\n"
        f"<b>• Duration:</b> <code>{duration_str}</code>\n"
        f"<b>• File ID:</b> <code>{file_id}</code>\n"
        f"<b>• Caption:</b> {caption_str}\n\n"
        f"<b>• Source Chat:</b> {source_display}\n"
        f"<b>• Source Chat ID:</b> <code>{source_id}</code>\n"
        f"{sender_block}"
        f"<b>• Indexed DB Link:</b> {db_msg_display}\n"
        f"<b>• Time:</b> <code>{timestamp}</code>"
    )

    send_kwargs = {
        "chat_id": int(log_group_id),
        "text": log_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if index_topic_id:
        send_kwargs["message_thread_id"] = int(index_topic_id)

    try:
        await bot.send_message(**send_kwargs)
    except Exception as e:
        print(f"[INDEX_LOG_SENDER ERROR] Failed to send index log: {e}")
