import html
from telebot.async_telebot import AsyncTeleBot
import config.settings as settings
from functions.script_engine.script_sender import send_script_message


async def send_index_log(bot: AsyncTeleBot, record: dict) -> None:
    """Sends a formatted log message to INDEX_LOG_TOPIC_ID inside LOG_GROUP_ID when a file is indexed."""
    if not settings.LOG_GROUP_ID:
        return

    try:
        book_meta = record.get("book_meta") or {}
        placeholders = {
            "file_name": html.escape(str(record.get("file_name") or "Unknown")),
            "file_size": html.escape(str(record.get("file_size_str") or "0 B")),
            "file_id": html.escape(str(record.get("file_id") or "")),
            "extension": html.escape(str(record.get("extension") or "unknown")),
            "file_type": html.escape(str(record.get("file_type") or "Document")),
            "duration": html.escape(str(record.get("duration_str") or "N/A")),
            "caption": html.escape(str(record.get("caption") or "None")[:200]),
            "chat_title": html.escape(str(record.get("source_chat_title") or "Channel")),
            "chat_id": html.escape(str(record.get("source_chat_id") or "")),
            "topic_id": html.escape(str(record.get("topic_id") or "None")),
            "db_message_id": html.escape(str(record.get("db_message_id") or "N/A")),
            "book_title": html.escape(str(book_meta.get("book_title") or "N/A")),
            "book_author": html.escape(str(book_meta.get("book_author") or "N/A")),
            "book_rating": html.escape(str(book_meta.get("book_rating") or "N/A")),
            "book_genres": html.escape(str(book_meta.get("book_genres") or "N/A")),
        }

        await send_script_message(
            bot=bot,
            chat_id=settings.LOG_GROUP_ID,
            script_key="file_index_log",
            placeholders=placeholders,
            message_thread_id=settings.INDEX_LOG_TOPIC_ID,
            allow_media=False,
        )
    except Exception as e:
        print(f"[INDEX LOG SENDER ERROR] {e}")
