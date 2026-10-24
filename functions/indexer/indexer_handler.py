from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
import config.settings as settings
from database.files_database.files_db import is_file_already_indexed, save_indexed_file
from functions.indexer.index_log_sender import send_index_log


MIME_TO_EXT = {
    "application/epub+zip": "epub",
    "application/pdf": "pdf",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/mp4": "m4b",
    "audio/x-m4b": "m4b",
    "audio/x-m4a": "m4b",
    "audio/vnd.audible.aax": "aax",
}


def extract_media_info(message: Message) -> dict | None:
    """
    Inspects a Telegram message for a supported eBook or Audiobook (document or audio).
    Returns a dictionary of file attributes if supported, or None otherwise.
    """
    media = None
    default_name = "Unknown_File"
    duration = None

    if message.document:
        media = message.document
        default_name = "Unknown_Book"
    elif message.audio:
        media = message.audio
        duration = getattr(media, "duration", None)
        title = getattr(media, "title", None)
        performer = getattr(media, "performer", None)
        if performer and title:
            default_name = f"{performer} - {title}"
        elif title:
            default_name = title
        else:
            default_name = "Unknown_Audiobook"

    if not media:
        return None

    raw_file_name = getattr(media, "file_name", None) or default_name
    mime_type = (getattr(media, "mime_type", None) or "").lower()

    # Extract file extension
    ext = ""
    if "." in raw_file_name:
        ext = raw_file_name.rsplit(".", 1)[-1].lower().strip()

    # Fallback to MIME type if filename had no extension (common on some Telegram audio uploads)
    if ext not in settings.ALLOWED_EXTENSIONS and mime_type in MIME_TO_EXT:
        ext = MIME_TO_EXT[mime_type]
        if "." not in raw_file_name:
            raw_file_name = f"{raw_file_name}.{ext}"

    if ext not in settings.ALLOWED_EXTENSIONS:
        return None

    file_type = "audiobook" if ext in settings.AUDIOBOOK_EXTENSIONS else "ebook"

    return {
        "file_id": media.file_id,
        "file_unique_id": media.file_unique_id,
        "file_name": raw_file_name,
        "file_size": getattr(media, "file_size", 0) or 0,
        "caption": message.caption or "",
        "duration": duration,
        "file_extension": ext,
        "file_type": file_type,
    }


def extract_sender_details(message: Message) -> dict:
    """
    Extracts sender user title/name, username, and user ID when a file is
    directly uploaded or forwarded into the Index Database Channel.
    """
    user = getattr(message, "from_user", None) or getattr(message, "forward_from", None)
    sender_id = None
    sender_name = None
    sender_username = None

    if user:
        sender_id = user.id
        first = getattr(user, "first_name", "") or ""
        last = getattr(user, "last_name", "") or ""
        sender_name = f"{first} {last}".strip() or getattr(user, "full_name", None)
        sender_username = getattr(user, "username", None)

    author_signature = getattr(message, "author_signature", None)

    return {
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_username": sender_username,
        "author_signature": author_signature,
    }


async def handle_incoming_media(bot: AsyncTeleBot, message: Message) -> None:
    """
    Processes incoming documents and audio files from channels and groups:
    1. Validates extension (EPUB, PDF, AZW3, KFX, MP3, M4B, AAX).
    2. Checks if already indexed via file_unique_id.
    3. Forwards to INDEX_CHANNEL_ID (unless already posted directly inside INDEX_CHANNEL_ID).
    4. Saves metadata to MongoDB and sends an HTML log to INDEX_LOG_TOPIC_ID.
    """
    index_channel_id = getattr(settings, "INDEX_CHANNEL_ID", None)
    if not index_channel_id:
        return

    chat_id = message.chat.id
    file_sharing_channel_id = getattr(settings, "FILE_SHARING_CHANNEL_ID", None)
    log_group_id = getattr(settings, "LOG_GROUP_ID", None)

    # Do not index temporary files in the File Sharing Channel or Log Group
    if chat_id in (file_sharing_channel_id, log_group_id):
        return

    media_info = extract_media_info(message)
    if not media_info:
        return

    # Skip if this exact file is already in the database
    existing = await is_file_already_indexed(media_info["file_unique_id"])
    if existing:
        return

    is_direct_upload = (int(chat_id) == int(index_channel_id))
    db_channel_username = None

    if is_direct_upload:
        # File was uploaded directly to the Indexed File Database Channel
        db_message_id = message.message_id
        db_channel_username = getattr(message.chat, "username", None)
    else:
        # File was posted in another channel or group -> forward to Indexed File Database Channel
        try:
            forwarded_msg = await bot.forward_message(
                chat_id=int(index_channel_id),
                from_chat_id=chat_id,
                message_id=message.message_id,
            )
            db_message_id = forwarded_msg.message_id
            db_channel_username = getattr(forwarded_msg.chat, "username", None)

            # Update file_id from the forwarded message in the storage channel
            forwarded_media = getattr(forwarded_msg, "document", None) or getattr(forwarded_msg, "audio", None)
            if forwarded_media and getattr(forwarded_media, "file_id", None):
                media_info["file_id"] = forwarded_media.file_id
        except Exception as e:
            print(f"[INDEXER FORWARD ERROR] Failed to forward message {message.message_id} from {chat_id}: {e}")
            return

    record_to_save = {
        **media_info,
        "db_channel_id": int(index_channel_id),
        "db_message_id": db_message_id,
        "source_chat_id": chat_id,
        "source_chat_title": getattr(message.chat, "title", None) or "Private Chat",
        "source_chat_username": getattr(message.chat, "username", None),
        "source_message_id": message.message_id,
        "is_direct_upload": is_direct_upload,
    }

    is_inserted, saved_doc = await save_indexed_file(record_to_save)
    if not is_inserted:
        return

    sender_info = extract_sender_details(message) if is_direct_upload else {}

    log_payload = {
        **saved_doc,
        **sender_info,
        "db_channel_username": db_channel_username,
    }
    await send_index_log(bot, log_payload)


def register_indexer_handler(bot: AsyncTeleBot) -> None:
    """Registers automatic media indexing handlers for channels and groups."""

    @bot.channel_post_handler(content_types=["document", "audio"])
    async def channel_media_listener(message: Message):
        await handle_incoming_media(bot, message)

    @bot.message_handler(
        chat_types=["group", "supergroup"],
        content_types=["document", "audio"],
    )
    async def group_media_listener(message: Message):
        await handle_incoming_media(bot, message)
