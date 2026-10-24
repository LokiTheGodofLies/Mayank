import asyncio
import html
import uuid
from datetime import datetime, timezone, timedelta

from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import config.settings as settings
from database.connection import db
from database.files_database.files_db import save_indexed_file
from functions.indexer.index_log_sender import send_index_log

IST = timezone(timedelta(hours=5, minutes=30))

PENDING_BATCHES: dict[int, dict] = {}
PENDING_NOTE_INPUT: dict[int, str] = {}

SUPPORTED_EXTENSIONS = getattr(settings, "ALLOWED_EXTENSIONS", {
    "epub", "pdf", "zip", "mp3", "m4b", "aax"
})
AUDIOBOOK_EXTENSIONS = getattr(settings, "AUDIOBOOK_EXTENSIONS", {"mp3", "m4b", "aax"})


def get_ist_time() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def get_owner_ids() -> list[int]:
    owners = getattr(settings, "OWNER_IDS", []) or []
    return [int(uid) for uid in owners if str(uid).strip()]


def _supported_media_data(message: Message) -> dict | None:
    media = getattr(message, "document", None) or getattr(message, "audio", None)
    if not media:
        return None

    raw_name = getattr(media, "file_name", None) or getattr(media, "title", None) or "Unknown_File"
    mime_type = (getattr(media, "mime_type", None) or "").lower()
    ext = ""
    if "." in str(raw_name):
        ext = str(raw_name).rsplit(".", 1)[-1].lower().strip()

    if not ext and mime_type:
        mime_to_ext = {
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
        ext = mime_to_ext.get(mime_type, "")
        if ext and "." not in str(raw_name):
            raw_name = f"{raw_name}.{ext}"

    if ext not in SUPPORTED_EXTENSIONS:
        return None

    file_type = "audiobook" if ext in AUDIOBOOK_EXTENSIONS else "ebook"
    return {
        "file_id": getattr(media, "file_id", None),
        "file_unique_id": getattr(media, "file_unique_id", None) or getattr(media, "file_id", None),
        "file_name": raw_name,
        "file_size": int(getattr(media, "file_size", 0) or 0),
        "caption": getattr(message, "caption", None) or "",
        "duration": getattr(media, "duration", None),
        "file_extension": ext,
        "file_type": file_type,
        "source_chat_id": message.chat.id,
        "source_chat_title": getattr(message.chat, "title", None) or "Private Chat",
        "source_chat_username": getattr(message.chat, "username", None),
        "source_message_id": message.message_id,
        "topic_id": getattr(message, "message_thread_id", None),
        "uploader_title": (
            getattr(message.from_user, "full_name", None)
            or getattr(message.from_user, "first_name", None)
            or "Unknown User"
        ),
        "uploader_username": getattr(message.from_user, "username", None),
        "uploader_id": getattr(message.from_user, "id", None),
        "uploaded_at": get_ist_time(),
    }


def _make_confirm_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Yes", callback_data="idx_review:confirm_yes"),
        InlineKeyboardButton("❌ No", callback_data="idx_review:confirm_no"),
    )
    return markup


def _make_more_files_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Yes", callback_data="idx_review:more_yes"),
        InlineKeyboardButton("✅ Done", callback_data="idx_review:more_done"),
    )
    return markup


def _make_note_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Yes", callback_data="idx_review:note_yes"),
        InlineKeyboardButton("❌ No", callback_data="idx_review:note_no"),
    )
    return markup


def _make_submit_markup(user_id: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📤 Submit", callback_data=f"idx_review:submit:{user_id}"),
    )
    return markup


def _make_review_markup(request_id: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Approve", callback_data=f"idx_review:approve:{request_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"idx_review:reject:{request_id}"),
    )
    return markup


async def _store_pending_request(file_record: dict, user_id: int, note: str = "", status: str = "pending") -> str:
    if db is None:
        return ""

    request_id = uuid.uuid4().hex
    request = {
        "request_id": request_id,
        "user_id": user_id,
        "status": status,
        "note": note,
        "file_data": file_record,
        "created_at": get_ist_time(),
    }
    await db["pending_index_requests"].insert_one(request)
    return request_id


async def _submit_batch_to_owner(bot: AsyncTeleBot, user_id: int) -> None:
    batch = PENDING_BATCHES.get(user_id)
    if not batch or not batch.get("files"):
        return

    owners = get_owner_ids()
    if not owners:
        await bot.send_message(user_id, "⚠️ No owner is configured for review approvals.")
        return

    for file_record in batch["files"]:
        request_id = await _store_pending_request(
            file_record=file_record,
            user_id=user_id,
            note=batch.get("note", ""),
            status="pending",
        )
        if not request_id:
            continue

        file_name = html.escape(file_record["file_name"])
        note_text = batch.get("note") or "No notes added."
        caption = (
            f"<b>Pending Index Review</b>\n"
            f"<b>File:</b> <code>{file_name}</code>\n"
            f"<b>Uploader:</b> {html.escape(str(file_record.get('uploader_title', 'Unknown User')))}\n"
            f"<b>Username:</b> @{html.escape(str(file_record.get('uploader_username') or 'unknown'))}\n"
            f"<b>User ID:</b> <code>{file_record.get('uploader_id', 'N/A')}</code>\n\n"
            f"<b>Note:</b> {html.escape(note_text[:1000])}"
        )

        for owner_id in owners:
            try:
                if file_record["file_type"] == "audiobook":
                    await bot.send_audio(
                        chat_id=owner_id,
                        audio=file_record["file_id"],
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=_make_review_markup(request_id),
                    )
                else:
                    await bot.send_document(
                        chat_id=owner_id,
                        data=file_record["file_id"],
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=_make_review_markup(request_id),
                    )
            except Exception:
                pass

    await bot.send_message(user_id, "📬 Your file request has been sent to the owner for approval.")
    PENDING_BATCHES.pop(user_id, None)
    PENDING_NOTE_INPUT.pop(user_id, None)


async def approve_pending_request(bot: AsyncTeleBot, request_id: str, owner_user: object) -> bool:
    if db is None:
        return False

    request = await db["pending_index_requests"].find_one({"request_id": request_id})
    if not request:
        return False

    if request.get("status") != "pending":
        return False

    file_record = request.get("file_data") or {}
    owner_title = (
        getattr(owner_user, "full_name", None)
        or getattr(owner_user, "first_name", None)
        or "Owner"
    )
    owner_username = getattr(owner_user, "username", None)
    owner_id = getattr(owner_user, "id", None)

    final_record = {
        **file_record,
        "uploader_title": file_record.get("uploader_title"),
        "uploader_username": file_record.get("uploader_username"),
        "uploader_id": file_record.get("uploader_id"),
        "uploaded_at": file_record.get("uploaded_at") or get_ist_time(),
        "approved_by_owner_title": owner_title,
        "approved_by_owner_username": owner_username,
        "approved_by_owner_id": owner_id,
        "approved_at": get_ist_time(),
    }

    await save_indexed_file(final_record)
    await db["pending_index_requests"].update_one(
        {"request_id": request_id},
        {"$set": {"status": "approved", "approved_at": get_ist_time(), "approved_by_owner_id": owner_id}},
    )

    try:
        await send_index_log(bot, final_record)
    except Exception:
        pass

    return True


async def reject_pending_request(bot: AsyncTeleBot, request_id: str) -> bool:
    if db is None:
        return False

    result = await db["pending_index_requests"].update_one(
        {"request_id": request_id},
        {"$set": {"status": "rejected", "resolved_at": get_ist_time()}},
    )
    return result.modified_count > 0


async def _reset_or_prompt(bot: AsyncTeleBot, user_id: int, message: Message, state_name: str = "awaiting_confirmation") -> None:
    batch = PENDING_BATCHES.get(user_id)
    if not batch:
        return
    batch["state"] = state_name


def _batch_files_for_user(user_id: int) -> list[dict]:
    batch = PENDING_BATCHES.get(user_id)
    if not batch:
        return []
    return list(batch.get("files") or [])


async def register_index_review_handler(bot: AsyncTeleBot) -> None:
    """User-to-owner approval workflow for private file submissions."""

    @bot.message_handler(content_types=["document", "audio"], chat_types=["private"])
    async def handle_private_pending_file(message: Message):
        if not message.from_user:
            return

        file_data = _supported_media_data(message)
        if not file_data:
            return

        user_id = message.from_user.id
        batch = PENDING_BATCHES.setdefault(user_id, {"files": [], "state": "idle", "note": ""})
        batch["files"].append(file_data)

        if batch.get("state") in {"idle", "awaiting_confirmation"}:
            batch["state"] = "awaiting_confirmation"
            await bot.send_message(
                user_id,
                "📚 Do you want to add these files to the bot database?",
                reply_markup=_make_confirm_markup(),
            )
        elif batch.get("state") == "awaiting_more":
            await bot.send_message(
                user_id,
                "📚 Do you want to add more files?",
                reply_markup=_make_more_files_markup(),
            )

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("idx_review:"))
    async def handle_index_review_callback(call: CallbackQuery):
        data = call.data or ""
        owner_ids = get_owner_ids()

        if data.startswith("idx_review:confirm_yes"):
            user_id = call.from_user.id
            batch = PENDING_BATCHES.get(user_id)
            if not batch:
                await bot.answer_callback_query(call.id, "No active batch found.")
                return
            batch["state"] = "awaiting_more"
            await bot.edit_message_text(
                text="📚 Do you want to add more files?",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=_make_more_files_markup(),
            )
            await bot.answer_callback_query(call.id)
            return

        if data.startswith("idx_review:confirm_no"):
            user_id = call.from_user.id
            PENDING_BATCHES.pop(user_id, None)
            PENDING_NOTE_INPUT.pop(user_id, None)
            await bot.edit_message_text(
                text="❌ No files were added.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
            )
            await bot.answer_callback_query(call.id)
            return

        if data.startswith("idx_review:more_yes"):
            user_id = call.from_user.id
            batch = PENDING_BATCHES.get(user_id)
            if not batch:
                await bot.answer_callback_query(call.id, "No active batch found.")
                return
            batch["state"] = "awaiting_more"
            await bot.answer_callback_query(call.id, "Send more files and then press Done when finished.")
            return

        if data.startswith("idx_review:more_done"):
            user_id = call.from_user.id
            batch = PENDING_BATCHES.get(user_id)
            if not batch:
                await bot.answer_callback_query(call.id, "No active batch found.")
                return
            batch["state"] = "awaiting_note_choice"
            await bot.edit_message_text(
                text="📝 Do you want to add notes/details about these files?",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=_make_note_markup(),
            )
            await bot.answer_callback_query(call.id)
            return

        if data.startswith("idx_review:note_yes"):
            user_id = call.from_user.id
            batch = PENDING_BATCHES.get(user_id)
            if not batch:
                await bot.answer_callback_query(call.id, "No active batch found.")
                return
            batch["state"] = "awaiting_note_text"
            await bot.edit_message_text(
                text="📄 Please include the information about these books and press Submit when done.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
            )
            await bot.answer_callback_query(call.id)
            return

        if data.startswith("idx_review:note_no"):
            user_id = call.from_user.id
            batch = PENDING_BATCHES.get(user_id)
            if not batch:
                await bot.answer_callback_query(call.id, "No active batch found.")
                return
            batch["note"] = ""
            await _submit_batch_to_owner(bot, user_id)
            await bot.answer_callback_query(call.id)
            return

        if data.startswith("idx_review:submit:"):
            _, _, user_id_str = data.split(":", 2)
            user_id = int(user_id_str)
            if call.from_user.id != user_id:
                await bot.answer_callback_query(call.id, "You cannot submit someone else’s request.")
                return
            batch = PENDING_BATCHES.get(user_id)
            if not batch:
                await bot.answer_callback_query(call.id, "No active batch found.")
                return
            await _submit_batch_to_owner(bot, user_id)
            await bot.answer_callback_query(call.id)
            return

        if data.startswith("idx_review:approve:"):
            if not call.from_user or call.from_user.id not in owner_ids:
                await bot.answer_callback_query(call.id, "🚫 You are not authorised. Only owners can access this.", show_alert=True)
                return

            _, _, request_id = data.split(":", 2)
            ok = await approve_pending_request(bot, request_id, call.from_user)
            if ok:
                await bot.answer_callback_query(call.id, "✅ File approved.")
                try:
                    await bot.edit_message_text(
                        text="✅ Approved by owner.",
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
            else:
                await bot.answer_callback_query(call.id, "This approval request is no longer valid.", show_alert=True)
            return

        if data.startswith("idx_review:reject:"):
            if not call.from_user or call.from_user.id not in owner_ids:
                await bot.answer_callback_query(call.id, "🚫 You are not authorised. Only owners can access this.", show_alert=True)
                return

            _, _, request_id = data.split(":", 2)
            ok = await reject_pending_request(bot, request_id)
            if ok:
                await bot.answer_callback_query(call.id, "❌ File rejected.")
                try:
                    await bot.edit_message_text(
                        text="❌ Rejected by owner.",
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
            else:
                await bot.answer_callback_query(call.id, "This review request is no longer valid.", show_alert=True)
            return

    @bot.message_handler(content_types=["text"], chat_types=["private"])
    async def handle_index_note_input(message: Message):
        if not message.from_user:
            return

        user_id = message.from_user.id
        batch = PENDING_BATCHES.get(user_id)
        if not batch or batch.get("state") != "awaiting_note_text":
            return

        note_text = (message.text or "").strip()
        if not note_text:
            await bot.send_message(user_id, "Please send a valid note or press No.")
            return

        batch["note"] = note_text
        batch["state"] = "note_ready"
        await bot.send_message(
            user_id,
            "✅ Your notes have been saved. Press Submit to send these files to the owner for approval.",
            reply_markup=_make_submit_markup(user_id),
        )


__all__ = [
    "register_index_review_handler",
    "approve_pending_request",
    "reject_pending_request",
]
