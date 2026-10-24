import asyncio
import html
import re
from typing import Any

from telebot.async_telebot import AsyncTeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import config.settings as settings
from config.strings import DEFAULT_SCRIPTS
from database.files_database.files_db import (
    get_file_by_unique_id,
    is_file_already_indexed,
    save_indexed_file,
    update_indexed_file_channel_msg,
    get_ist_time,
)
from functions.indexer.index_log_sender import send_index_log
from functions.error_logger.error_log_sender import (
    send_bot_not_admin_log,
    send_missing_var_log,
    send_error_log,
)

MIME_TO_EXT = {
    "application/epub+zip": "epub",
    "application/pdf": "pdf",
    "application/zip": "zip",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/mp4": "m4b",
    "audio/x-m4b": "m4b",
    "audio/x-m4a": "m4b",
    "audio/vnd.audible.aax": "aax",
}

_INDEX_BATCH_SIZE = 10
_INDEX_BATCH_PAUSE_SECONDS = 10
_INDEX_FILE_DELAY_SECONDS = 3

_BOT_ID_CACHE: int | None = None

# Stores active batch /index jobs keyed by status_message_id: {"paused": bool, "cancelled": bool}
ACTIVE_INDEX_JOBS: dict[int, dict] = {}


def is_admin_or_owner(user_id: int) -> bool:
    """Checks if a user is in OWNER_IDS or ADMIN_IDS."""
    owners = getattr(settings, "OWNER_IDS", []) or []
    admins = getattr(settings, "ADMIN_IDS", []) or []
    allowed = {int(uid) for uid in (owners + admins)}
    return int(user_id) in allowed


async def is_bot_admin_in_chat(bot: AsyncTeleBot, chat_id: int) -> bool:
    """Checks whether the bot is an administrator in the given channel or group."""
    global _BOT_ID_CACHE
    try:
        if _BOT_ID_CACHE is None:
            me = await bot.get_me()
            _BOT_ID_CACHE = me.id
        member = await bot.get_chat_member(chat_id, _BOT_ID_CACHE)
        return getattr(member, "status", "") in ("administrator", "creator")
    except Exception:
        return False


async def wait_for_flood_or_retry(exc: Exception, *, default_wait: int = 5) -> bool:
    """Handles Telegram 429 flood-wait responses without crashing the batch loop."""
    if not isinstance(exc, ApiTelegramException):
        return False

    text = str(exc).lower()
    if "flood" not in text and "retry after" not in text and "too many requests" not in text and "429" not in text:
        return False

    retry_after = default_wait
    match = re.search(r"retry after\s+(\d+)", text, re.IGNORECASE)
    if match:
        try:
            retry_after = max(1, int(match.group(1)))
        except ValueError:
            retry_after = default_wait

    # Stop the current batch immediately. The queue will resume later with the remaining files.
    await asyncio.sleep(retry_after)
    return True


async def verify_msg_exists_in_index_channel(bot: AsyncTeleBot, index_channel_id: int, db_message_id: int | None) -> bool:
    """
    Verifies whether a previously indexed message ID still exists inside INDEX_CHANNEL_ID.
    Returns True if it exists, or False if it was deleted or missing.
    """
    if not db_message_id or not index_channel_id:
        return False
    try:
        await bot.set_message_reaction(
            chat_id=int(index_channel_id),
            message_id=int(db_message_id),
            reaction=[],
        )
        return True
    except Exception as e:
        err_str = str(e).upper()
        if "MESSAGE_ID_INVALID" in err_str or "MESSAGE TO REACT NOT FOUND" in err_str or "MESSAGE NOT FOUND" in err_str:
            return False
        return True


def extract_media_info(message: Message) -> dict | None:
    """
    Inspects a Telegram message for a supported eBook or Audiobook (document or audio).
    Returns a dictionary of file attributes if supported, or None otherwise.
    """
    media = None
    default_name = "Unknown_File"
    duration = None

    if getattr(message, "document", None):
        media = message.document
        default_name = "Unknown_Book"
    elif getattr(message, "audio", None):
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

    ext = ""
    if "." in raw_file_name:
        ext = raw_file_name.rsplit(".", 1)[-1].lower().strip()

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
        "caption": getattr(message, "caption", None) or "",
        "duration": duration,
        "file_extension": ext,
        "file_type": file_type,
    }


def extract_sender_details(message: Message) -> dict:
    """Extracts sender user title/name, username, and user ID for direct uploads to INDEX_CHANNEL_ID."""
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


def caption_has_metadata(caption: str | None, book_meta: dict | None) -> bool:
    """Returns True if the caption already has metadata-like content; otherwise the file is repaired first."""
    text = (caption or "").strip()
    if not text:
        return False

    lowered = text.lower()
    keyword_hits = (
        "title",
        "author",
        "genre",
        "pages",
        "rating",
        "isbn",
        "published",
        "year",
        "book",
    )
    if any(keyword in lowered for keyword in keyword_hits):
        return True

    if isinstance(book_meta, dict):
        values = [book_meta.get("book_title"), book_meta.get("book_author"), book_meta.get("isbn")]
        if any(value and str(value).strip() for value in values):
            return True

    return False


def build_metadata_caption(media_info: dict, book_meta: dict | None = None) -> str:
    """Builds a fallback metadata caption when Goodreads-style details are missing."""
    title = (book_meta or {}).get("book_title") or media_info.get("file_name") or "Unknown Book"
    author = (book_meta or {}).get("book_author") or "Unknown Author"
    file_type = (media_info.get("file_type") or "ebook").upper()
    extension = (media_info.get("file_extension") or "").upper() or "FILE"
    size = media_info.get("file_size", 0) or 0
    duration = media_info.get("duration")

    lines = [
        f"<b>{html.escape(str(title))}</b>",
        f"<b>Author:</b> {html.escape(str(author))}",
        f"<b>Type:</b> {html.escape(file_type)}",
        f"<b>Extension:</b> <code>{html.escape(extension)}</code>",
        f"<b>Size:</b> <code>{size}</code> bytes",
    ]
    if duration:
        lines.append(f"<b>Duration:</b> <code>{duration}</code>")

    return "\n".join(lines)


async def ensure_file_metadata_caption(bot: AsyncTeleBot, message: Message, media_info: dict) -> bool:
    """Ensures the stored file record has a metadata caption before considering it fully indexed."""
    file_unique_id = media_info.get("file_unique_id") or media_info.get("file_id")
    if not file_unique_id:
        return False

    record = await get_file_by_unique_id(file_unique_id)
    if not record:
        return False

    caption = record.get("caption") or ""
    book_meta = record.get("book_meta") or {}
    if caption_has_metadata(caption, book_meta):
        return True

    fallback_caption = build_metadata_caption(media_info, book_meta)
    record["caption"] = fallback_caption
    record["book_meta"] = book_meta
    record["updated_at"] = get_ist_time()
    await save_indexed_file(record)
    return True


async def process_single_file_dual_check(
    bot: AsyncTeleBot,
    message: Message,
    send_log: bool = True,
) -> str:
    """
    Runs Dual-Check indexing on a single message:
    Returns one of:
        - "filtered"  : Not a supported eBook/Audiobook
        - "duplicate" : Exists in BOTH INDEX_CHANNEL_ID and MongoDB
        - "forwarded" : Newly forwarded/indexed (or re-synced to MongoDB / INDEX_CHANNEL_ID)
        - "error"     : Failed due to permissions or missing config
    """
    index_channel_id = getattr(settings, "INDEX_CHANNEL_ID", None)
    if not index_channel_id:
        await send_missing_var_log(bot, ["INDEX_CHANNEL_ID"], context_action="File Indexing")
        return "error"

    media_info = extract_media_info(message)
    if not media_info:
        return "filtered"

    chat_id = message.chat.id
    is_direct_upload = (int(chat_id) == int(index_channel_id))
    existing_doc = await is_file_already_indexed(media_info["file_unique_id"])

    if existing_doc:
        recorded_msg_id = existing_doc.get("db_message_id")
        if is_direct_upload:
            await ensure_file_metadata_caption(bot, message, media_info)
            return "duplicate"

        still_in_channel = await verify_msg_exists_in_index_channel(
            bot=bot,
            index_channel_id=int(index_channel_id),
            db_message_id=recorded_msg_id,
        )
        if still_in_channel:
            await ensure_file_metadata_caption(bot, message, media_info)
            return "duplicate"

        try:
            forwarded_msg = await bot.forward_message(
                chat_id=int(index_channel_id),
                from_chat_id=chat_id,
                message_id=message.message_id,
            )
            forwarded_media = getattr(forwarded_msg, "document", None) or getattr(forwarded_msg, "audio", None)
            new_file_id = getattr(forwarded_media, "file_id", None) if forwarded_media else media_info["file_id"]
            await update_indexed_file_channel_msg(
                file_unique_id=media_info["file_unique_id"],
                db_channel_id=int(index_channel_id),
                db_message_id=forwarded_msg.message_id,
                new_file_id=new_file_id,
            )
            await ensure_file_metadata_caption(bot, message, media_info)
            return "forwarded"
        except Exception as e:
            if await wait_for_flood_or_retry(e):
                return "error"
            await send_bot_not_admin_log(
                bot=bot,
                chat_title=getattr(message.chat, "title", "Chat"),
                chat_id=chat_id,
                missing_permission=f"Forward to INDEX_CHANNEL_ID failed ({e})",
                action="Dual-Check Re-Forward",
                chat_username=getattr(message.chat, "username", None),
            )
            return "error"

    # Missing from MongoDB or not yet indexed
    db_channel_username = None
    if is_direct_upload:
        db_message_id = message.message_id
        db_channel_username = getattr(message.chat, "username", None)
    else:
        try:
            forwarded_msg = await bot.forward_message(
                chat_id=int(index_channel_id),
                from_chat_id=chat_id,
                message_id=message.message_id,
            )
            db_message_id = forwarded_msg.message_id
            db_channel_username = getattr(forwarded_msg.chat, "username", None)

            forwarded_media = getattr(forwarded_msg, "document", None) or getattr(forwarded_msg, "audio", None)
            if forwarded_media and getattr(forwarded_media, "file_id", None):
                media_info["file_id"] = forwarded_media.file_id
        except Exception as e:
            if await wait_for_flood_or_retry(e):
                return "error"
            await send_bot_not_admin_log(
                bot=bot,
                chat_title=getattr(message.chat, "title", "Chat"),
                chat_id=chat_id,
                missing_permission=f"Forward to INDEX_CHANNEL_ID failed ({e})",
                action="Auto/Batch Indexing",
                chat_username=getattr(message.chat, "username", None),
            )
            return "error"

    record_to_save = {
        **media_info,
        "db_channel_id": int(index_channel_id),
        "db_message_id": db_message_id,
        "source_chat_id": chat_id,
        "source_chat_title": getattr(message.chat, "title", None) or "Private Chat",
        "source_chat_username": getattr(message.chat, "username", None),
        "source_message_id": message.message_id,
        "topic_id": getattr(message, "message_thread_id", None),
        "is_direct_upload": is_direct_upload,
    }

    is_inserted, saved_doc = await save_indexed_file(record_to_save)
    await ensure_file_metadata_caption(bot, message, media_info)

    if is_inserted and send_log:
        sender_info = extract_sender_details(message) if is_direct_upload else {}
        log_payload = {
            **saved_doc,
            **sender_info,
            "db_channel_username": db_channel_username,
        }
        await send_index_log(bot, log_payload)

    return "forwarded"


async def handle_incoming_media(bot: AsyncTeleBot, message: Message) -> None:
    """
    Live listener for any channel or group where the bot is admin (except LOG_GROUP_ID).
    """
    chat_id = message.chat.id
    log_group_id = getattr(settings, "LOG_GROUP_ID", None)

    if log_group_id and int(chat_id) == int(log_group_id):
        return

    media_info = extract_media_info(message)
    if not media_info:
        return

    if not await is_bot_admin_in_chat(bot, chat_id):
        await send_bot_not_admin_log(
            bot=bot,
            chat_title=getattr(message.chat, "title", "Unknown Chat"),
            chat_id=chat_id,
            missing_permission="Administrator",
            action="Live File Indexing",
            chat_username=getattr(message.chat, "username", None),
        )
        return

    await process_single_file_dual_check(bot, message, send_log=True)


def build_batch_control_keyboard(job_id: int, is_paused: bool = False) -> InlineKeyboardMarkup:
    """Builds the [ ⏸ Pause / ▶️ Resume ] and [ ❌ Cancel ] buttons for /index."""
    markup = InlineKeyboardMarkup()
    pause_btn = (
        InlineKeyboardButton("▶️ Resume", callback_data=f"idxctl:resume:{job_id}")
        if is_paused
        else InlineKeyboardButton("⏸ Pause", callback_data=f"idxctl:pause:{job_id}")
    )
    cancel_btn = InlineKeyboardButton("❌ Cancel", callback_data=f"idxctl:cancel:{job_id}")
    markup.row(pause_btn, cancel_btn)
    return markup


def render_progress_box(stats: dict, status_label: str, footer_label: str) -> str:
    """Formats the ╔════❰ ғᴏʀᴡᴀʀᴅ sᴛᴀᴛᴜs  ❱═❍⊱❁۪۪ progress box."""
    total_to_process = max(1, stats["total_messages"])
    pct = min(100, int((stats["fetched"] / total_to_process) * 100))
    template = DEFAULT_SCRIPTS.get("forward_status", "")
    return template.format(
        fetched=stats["fetched"],
        remaining=max(0, stats["remaining"]),
        forwarded=stats["forwarded"],
        duplicate=stats["duplicate"],
        deleted=stats["deleted"],
        skipped=stats["skipped"],
        filtered=stats["filtered"],
        status=status_label,
        percentage=pct,
        footer=footer_label,
    )


def parse_chat_and_msg_link(link_or_id: str) -> tuple[int | str | None, int | None]:
    """
    Parses a Telegram message link (https://t.me/c/123456/500 or https://t.me/username/500)
    or a plain chat ID / @username.
    """
    text = link_or_id.strip()
    priv_match = re.match(r"https?://t\.me/c/(\d+)/(\d+)", text)
    if priv_match:
        return int(f"-100{priv_match.group(1)}"), int(priv_match.group(2))

    pub_match = re.match(r"https?://t\.me/([a-zA-Z0-9_]+)/(\d+)", text)
    if pub_match:
        return f"@{pub_match.group(1)}", int(pub_match.group(2))

    if text.lstrip("-").isdigit():
        return int(text), None

    if text.startswith("@"):
        return text, None

    return text, None


async def process_index_batch(
    bot: AsyncTeleBot,
    *,
    source_chat_id: int | str,
    last_msg_id: int,
    skip_msg_id: int = 0,
    filter_topic_id: int | None = None,
    chat_obj: Any | None = None,
    resolved_chat_id: int | str | None = None,
    log_group_id: int | None = None,
    status_msg: Message | None = None,
    job_id: int | None = None,
) -> dict:
    """Safely processes files one-by-one with a max burst of 10 items and a 10s pause after each batch."""
    stats = {
        "total_messages": last_msg_id,
        "fetched": 0,
        "remaining": last_msg_id,
        "forwarded": 0,
        "duplicate": 0,
        "deleted": 0,
        "skipped": 0,
        "filtered": 0,
    }

    if status_msg is None or job_id is None:
        return stats

    probe_chat_id = int(log_group_id) if log_group_id else getattr(status_msg.chat, "id", 0)

    for msg_id in range(1, last_msg_id + 1):
        job_state = ACTIVE_INDEX_JOBS.get(job_id)
        if not job_state or job_state.get("cancelled"):
            break

        while job_state.get("paused") and not job_state.get("cancelled"):
            await asyncio.sleep(1.5)
            job_state = ACTIVE_INDEX_JOBS.get(job_id)
            if not job_state:
                break

        if not job_state or job_state.get("cancelled"):
            break

        stats["fetched"] += 1
        stats["remaining"] = last_msg_id - stats["fetched"]

        if msg_id <= skip_msg_id:
            stats["skipped"] += 1
            continue

        try:
            probed_msg = await bot.forward_message(
                chat_id=probe_chat_id,
                from_chat_id=resolved_chat_id,
                message_id=msg_id,
                disable_notification=True,
            )
        except Exception as e:
            if await wait_for_flood_or_retry(e):
                continue
            err_u = str(e).upper()
            if "MESSAGE TO FORWARD NOT FOUND" in err_u or "MESSAGE_ID_INVALID" in err_u:
                stats["deleted"] += 1
            else:
                stats["filtered"] += 1
            continue

        try:
            await bot.delete_message(chat_id=probe_chat_id, message_id=probed_msg.message_id)
        except Exception:
            pass

        if filter_topic_id is not None and getattr(probed_msg, "message_thread_id", None) != filter_topic_id:
            stats["skipped"] += 1
            continue

        probed_msg.chat = chat_obj
        probed_msg.message_id = msg_id

        # Enforce the rule: every file must exist in the index channel, in MongoDB, and have a metadata caption.
        # If any check fails, repair that file first and do not move to the next one.
        repaired = await ensure_file_metadata_caption(bot, probed_msg, extract_media_info(probed_msg) or {})
        if not repaired:
            # If the file is unsupported, skip it cleanly.
            if not extract_media_info(probed_msg):
                stats["filtered"] += 1
                await asyncio.sleep(_INDEX_FILE_DELAY_SECONDS)
                continue

        outcome = await process_single_file_dual_check(bot, probed_msg, send_log=True)
        if outcome == "forwarded":
            stats["forwarded"] += 1
        elif outcome == "duplicate":
            stats["duplicate"] += 1
        else:
            stats["filtered"] += 1

        # A strict single-file queue: process one file completely before continuing.
        await asyncio.sleep(_INDEX_FILE_DELAY_SECONDS)

        if stats["fetched"] % _INDEX_BATCH_SIZE == 0 and msg_id != last_msg_id:
            await asyncio.sleep(_INDEX_BATCH_PAUSE_SECONDS)

        if stats["fetched"] % 15 == 0 or stats["fetched"] == last_msg_id:
            try:
                await bot.edit_message_text(
                    text=render_progress_box(stats, status_label="forwarding", footer_label="ᴘʀᴏɢʀᴇssɪɴɢ"),
                    chat_id=status_msg.chat.id,
                    message_id=job_id,
                    parse_mode="HTML",
                    reply_markup=build_batch_control_keyboard(job_id, is_paused=job_state.get("paused", False)),
                )
            except Exception:
                pass

    return stats


def register_indexer_handler(bot: AsyncTeleBot) -> None:
    """Registers live indexing handlers and the batch /index command + Pause/Cancel callbacks."""

    @bot.channel_post_handler(content_types=["document", "audio"])
    async def channel_media_listener(message: Message):
        await handle_incoming_media(bot, message)

    @bot.message_handler(
        chat_types=["group", "supergroup"],
        content_types=["document", "audio"],
    )
    async def group_media_listener(message: Message):
        await handle_incoming_media(bot, message)

    @bot.message_handler(commands=["index"])
    async def handle_batch_index_command(message: Message):
        if not message.from_user or not is_admin_or_owner(message.from_user.id):
            await bot.reply_to(message, DEFAULT_SCRIPTS["access_denied"], parse_mode="HTML")
            return

        index_channel_id = getattr(settings, "INDEX_CHANNEL_ID", None)
        log_group_id = getattr(settings, "LOG_GROUP_ID", None)
        if not index_channel_id:
            await send_missing_var_log(bot, ["INDEX_CHANNEL_ID"], context_action="/index Command")
            await bot.reply_to(
                message,
                "⚠️ <b>INDEX_CHANNEL_ID is not configured!</b>",
                parse_mode="HTML",
            )
            return

        parts = (message.text or "").split()
        source_chat_id = None
        last_msg_id = None
        skip_msg_id = 0
        filter_topic_id = None

        if message.reply_to_message and getattr(message.reply_to_message, "forward_from_chat", None):
            source_chat_id = message.reply_to_message.forward_from_chat.id
            last_msg_id = message.reply_to_message.forward_from_message_id
            if len(parts) >= 2 and parts[1].isdigit():
                skip_msg_id = int(parts[1])
            if len(parts) >= 3 and parts[2].isdigit():
                filter_topic_id = int(parts[2])
        elif len(parts) >= 2:
            parsed_chat, parsed_msg = parse_chat_and_msg_link(parts[1])
            source_chat_id = parsed_chat
            if parsed_msg is not None:
                last_msg_id = parsed_msg
                if len(parts) >= 3 and parts[2].isdigit():
                    skip_msg_id = int(parts[2])
                if len(parts) >= 4 and parts[3].isdigit():
                    filter_topic_id = int(parts[3])
            elif len(parts) >= 3 and parts[2].isdigit():
                last_msg_id = int(parts[2])
                if len(parts) >= 4 and parts[3].isdigit():
                    skip_msg_id = int(parts[3])
                if len(parts) >= 5 and parts[4].isdigit():
                    filter_topic_id = int(parts[4])

        if not source_chat_id or not last_msg_id:
            await bot.reply_to(message, DEFAULT_SCRIPTS["index_usage"], parse_mode="HTML")
            return

        try:
            chat_obj = await bot.get_chat(source_chat_id)
            resolved_chat_id = chat_obj.id
            chat_title = getattr(chat_obj, "title", None) or str(source_chat_id)
        except Exception as e:
            await send_bot_not_admin_log(
                bot=bot,
                chat_title=str(source_chat_id),
                chat_id=str(source_chat_id),
                missing_permission=f"Bot cannot access chat ({e})",
                action="/index Command",
            )
            await bot.reply_to(
                message,
                f"❌ <b>Cannot access source chat:</b> <code>{html.escape(str(e))}</code>\n"
                "Make sure the bot is an Administrator in that channel/group.",
                parse_mode="HTML",
            )
            return

        if not await is_bot_admin_in_chat(bot, resolved_chat_id):
            await send_bot_not_admin_log(
                bot=bot,
                chat_title=chat_title,
                chat_id=resolved_chat_id,
                missing_permission="Administrator",
                action="/index Command",
                chat_username=getattr(chat_obj, "username", None),
            )
            await bot.reply_to(
                message,
                f"❌ <b>Bot is not an Administrator in {html.escape(chat_title)}!</b>",
                parse_mode="HTML",
            )
            return

        initial_text = render_progress_box(
            {
                "total_messages": last_msg_id,
                "fetched": 0,
                "remaining": last_msg_id,
                "forwarded": 0,
                "duplicate": 0,
                "deleted": 0,
                "skipped": 0,
                "filtered": 0,
            },
            status_label="forwarding",
            footer_label="ᴘʀᴏɢʀᴇssɪɴɢ",
        )
        status_msg = await bot.reply_to(message, initial_text, parse_mode="HTML")
        job_id = status_msg.message_id
        ACTIVE_INDEX_JOBS[job_id] = {"paused": False, "cancelled": False}

        await bot.edit_message_reply_markup(
            chat_id=status_msg.chat.id,
            message_id=job_id,
            reply_markup=build_batch_control_keyboard(job_id, is_paused=False),
        )

        try:
            stats = await process_index_batch(
                bot,
                source_chat_id=source_chat_id,
                last_msg_id=last_msg_id,
                skip_msg_id=skip_msg_id,
                filter_topic_id=filter_topic_id,
                chat_obj=chat_obj,
                resolved_chat_id=resolved_chat_id,
                log_group_id=log_group_id,
                status_msg=status_msg,
                job_id=job_id,
            )
        finally:
            ACTIVE_INDEX_JOBS.pop(job_id, None)

        final_state = ACTIVE_INDEX_JOBS.get(job_id, {"cancelled": False})
        if final_state.get("cancelled"):
            final_box = render_progress_box(stats, status_label="cancelled", footer_label="ᴄᴀɴᴄᴇʟʟᴇᴅ ❌")
            try:
                await bot.edit_message_text(
                    text=final_box,
                    chat_id=status_msg.chat.id,
                    message_id=job_id,
                    parse_mode="HTML",
                )
            except Exception:
                pass
            return

        completed_text = DEFAULT_SCRIPTS["index_completed"].format(
            chat_title=html.escape(chat_title),
            chat_id=resolved_chat_id,
            fetched=stats["fetched"],
            forwarded=stats["forwarded"],
            duplicate=stats["duplicate"],
            deleted=stats["deleted"],
            skipped=stats["skipped"],
            filtered=stats["filtered"],
            date_time=get_ist_time(),
        )
        try:
            await bot.edit_message_text(
                text=completed_text,
                chat_id=status_msg.chat.id,
                message_id=job_id,
                parse_mode="HTML",
            )
        except Exception:
            await bot.reply_to(message, completed_text, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("idxctl:"))
    async def handle_index_control_callback(call: CallbackQuery):
        if not call.from_user or not is_admin_or_owner(call.from_user.id):
            await bot.answer_callback_query(call.id, "Only Owners and Admins can control indexing!", show_alert=True)
            return

        _, action, job_id_str = call.data.split(":", 2)
        job_id = int(job_id_str)
        job = ACTIVE_INDEX_JOBS.get(job_id)

        if not job:
            await bot.answer_callback_query(call.id, "This indexing job has already finished.", show_alert=True)
            return

        if action == "pause":
            job["paused"] = True
            await bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=job_id,
                reply_markup=build_batch_control_keyboard(job_id, is_paused=True),
            )
            await bot.answer_callback_query(call.id, "⏸ Indexing paused.")
        elif action == "resume":
            job["paused"] = False
            await bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=job_id,
                reply_markup=build_batch_control_keyboard(job_id, is_paused=False),
            )
            await bot.answer_callback_query(call.id, "▶️ Indexing resumed.")
        elif action == "cancel":
            job["cancelled"] = True
            await bot.answer_callback_query(call.id, "❌ Cancelling indexing job...", show_alert=True)


if __name__ == "__main__":
    pass
