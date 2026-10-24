import asyncio
import hashlib
import html

from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import config.settings as settings
from database.files_database.files_db import get_file_by_id, search_indexed_files
from functions.script_engine.script_sender import send_script_message

SEARCH_QUERY_CACHE: dict[str, str] = {}

FILTER_CODE_TO_TYPE = {
    "a": None,
    "e": "ebook",
    "u": "audiobook",
}


def register_query_key(query_text: str) -> str:
    clean_query = query_text.strip()
    key = hashlib.md5(clean_query.lower().encode("utf-8")).hexdigest()[:8]
    SEARCH_QUERY_CACHE[key] = clean_query
    return key


def build_search_keyboard(
    results: list[dict],
    query_key: str,
    filter_code: str,
    current_page: int,
    total_pages: int,
    total_count: int,
) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()

    for doc in results:
        doc_id = str(doc.get("_id"))
        file_name = str(doc.get("file_name") or "Unknown File")
        file_type = str(doc.get("file_type") or "ebook").lower()
        prefix = "🎧" if file_type == "audiobook" else "📚"
        button_label = f"{prefix} {file_name}"
        if len(button_label) > 60:
            button_label = button_label[:57] + "..."
        markup.row(InlineKeyboardButton(text=button_label, callback_data=f"getfile:{doc_id}"))

    ebook_target = "a" if filter_code == "e" else "e"
    audio_target = "a" if filter_code == "u" else "u"
    ebook_btn_text = "📚 ✅" if filter_code == "e" else "📚"
    audio_btn_text = "🎧 ✅" if filter_code == "u" else "🎧"

    markup.row(
        InlineKeyboardButton(text=ebook_btn_text, callback_data=f"sfilt:{query_key}:{ebook_target}"),
        InlineKeyboardButton(text=audio_btn_text, callback_data=f"sfilt:{query_key}:{audio_target}"),
    )

    if total_count <= 10 or total_pages <= 1:
        markup.row(InlineKeyboardButton(text="1/1", callback_data="snoop"))
    else:
        prev_page = current_page - 1 if current_page > 1 else total_pages
        next_page = current_page + 1 if current_page < total_pages else 1
        markup.row(
            InlineKeyboardButton(text="Back", callback_data=f"spage:{query_key}:{filter_code}:{prev_page}"),
            InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="snoop"),
            InlineKeyboardButton(text="Next", callback_data=f"spage:{query_key}:{filter_code}:{next_page}"),
        )

    return markup


def format_search_header(query_text: str, filter_code: str, total_count: int, current_page: int, total_pages: int) -> str:
    escaped_q = html.escape(query_text)
    if filter_code == "e":
        mode_label = "eBooks Only 📚"
    elif filter_code == "u":
        mode_label = "Audiobooks Only 🎧"
    else:
        mode_label = "All Formats (📚 & 🎧)"

    if total_count == 0:
        return (
            f"🔍 <b>Search Query:</b> <code>{escaped_q}</code>\n"
            f"<b>Filter:</b> {mode_label}\n\n"
            f"<i>No matching files found for this filter.</i>"
        )

    return (
        f"🔍 <b>Search Results for:</b> <code>{escaped_q}</code>\n"
        f"<b>• Filter:</b> {mode_label}\n"
        f"<b>• Total Found:</b> <code>{total_count}</code>\n"
        f"<b>• Page:</b> <code>{current_page}/{total_pages}</code>\n\n"
        f"<i>Select a file below to send it to the File Sharing Channel:</i>"
    )


async def auto_delete_messages(bot: AsyncTeleBot, chat_id: int, message_ids: list[int], delay_seconds: int) -> None:
    await asyncio.sleep(delay_seconds)
    for msg_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            print(f"[AUTO DELETE ERROR] Could not delete message {msg_id} in {chat_id}: {e}")


def register_search_handler(bot: AsyncTeleBot) -> None:
    @bot.message_handler(commands=["search"])
    async def handle_search_command(message: Message):
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            await send_script_message(
                bot,
                chat_id=message.chat.id,
                script_key="search_usage",
                context={
                    "user_name": message.from_user.full_name if message.from_user else "User",
                    "user_link": f"tg://user?id={message.from_user.id}" if message.from_user else "",
                },
            )
            return

        query_text = parts[1].strip()
        query_key = register_query_key(query_text)
        filter_code = "a"

        results, total_count, total_pages = await search_indexed_files(
            query=query_text,
            file_type=None,
            page=1,
            per_page=10,
        )

        if total_count == 0:
            await send_script_message(
                bot,
                chat_id=message.chat.id,
                script_key="search_no_results",
                context={
                    "query": query_text,
                    "file_type": "All Formats",
                },
            )
            return

        header_text = format_search_header(
            query_text=query_text,
            filter_code=filter_code,
            total_count=total_count,
            current_page=1,
            total_pages=total_pages,
        )
        keyboard = build_search_keyboard(
            results=results,
            query_key=query_key,
            filter_code=filter_code,
            current_page=1,
            total_pages=total_pages,
            total_count=total_count,
        )

        await bot.reply_to(message, header_text, parse_mode="HTML", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data == "snoop")
    async def handle_noop_callback(call: CallbackQuery):
        await bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith(("spage:", "sfilt:")))
    async def handle_search_navigation(call: CallbackQuery):
        parts = call.data.split(":")
        action = parts[0]

        if action == "sfilt":
            _, query_key, filter_code = parts
            target_page = 1
        else:
            _, query_key, filter_code, page_str = parts
            target_page = int(page_str)

        query_text = SEARCH_QUERY_CACHE.get(query_key)
        if not query_text:
            await bot.answer_callback_query(call.id, "This search session expired. Please run /search again.", show_alert=True)
            return

        file_type = FILTER_CODE_TO_TYPE.get(filter_code)
        results, total_count, total_pages = await search_indexed_files(
            query=query_text,
            file_type=file_type,
            page=target_page,
            per_page=10,
        )

        header_text = format_search_header(
            query_text=query_text,
            filter_code=filter_code,
            total_count=total_count,
            current_page=target_page if total_count > 0 else 1,
            total_pages=total_pages,
        )
        keyboard = build_search_keyboard(
            results=results,
            query_key=query_key,
            filter_code=filter_code,
            current_page=target_page if total_count > 0 else 1,
            total_pages=total_pages,
            total_count=total_count,
        )

        try:
            await bot.edit_message_text(
                text=header_text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        except Exception:
            pass

        await bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("getfile:"))
    async def handle_file_selection(call: CallbackQuery):
        record_id = call.data.split(":", 1)[1]
        file_doc = await get_file_by_id(record_id)

        if not file_doc:
            await bot.answer_callback_query(call.id, "File not found in database.", show_alert=True)
            return

        file_sharing_channel_id = getattr(settings, "FILE_SHARING_CHANNEL_ID", None)
        index_channel_id = file_doc.get("db_channel_id") or getattr(settings, "INDEX_CHANNEL_ID", None)
        db_message_id = file_doc.get("db_message_id")

        if not file_sharing_channel_id:
            await bot.answer_callback_query(call.id, "FILE_SHARING_CHANNEL_ID is not configured.", show_alert=True)
            return

        if not index_channel_id or not db_message_id:
            await bot.answer_callback_query(call.id, "Source message details missing in database.", show_alert=True)
            return

        try:
            forwarded_file_msg = await bot.forward_message(
                chat_id=int(file_sharing_channel_id),
                from_chat_id=int(index_channel_id),
                message_id=int(db_message_id),
            )

            file_name = str(file_doc.get("file_name") or "Unknown")
            file_size = str(file_doc.get("file_size") or 0)
            duration = str(file_doc.get("duration") or "N/A")
            delete_minutes = int(getattr(settings, "FILE_AUTO_DELETE_SECONDS", 300) or 300) // 60

            notice_msg = await send_script_message(
                bot,
                chat_id=int(file_sharing_channel_id),
                script_key="file_delivery",
                context={
                    "file_name": file_name,
                    "file_size": file_size,
                    "duration": duration,
                    "delete_minutes": delete_minutes,
                },
                reply_to_message_id=forwarded_file_msg.message_id,
            )

            asyncio.create_task(
                auto_delete_messages(
                    bot=bot,
                    chat_id=int(file_sharing_channel_id),
                    message_ids=[forwarded_file_msg.message_id, notice_msg.message_id],
                    delay_seconds=int(getattr(settings, "FILE_AUTO_DELETE_SECONDS", 300) or 300),
                )
            )

            await bot.answer_callback_query(
                call.id,
                "File has been sent to the File Sharing Channel! It will be deleted in 5 minutes.",
                show_alert=True,
            )
        except Exception as e:
            print(f"[FILE DELIVERY ERROR] {e}")
            await bot.answer_callback_query(
                call.id,
                "Failed to forward file to the File Sharing Channel. Check bot permissions.",
                show_alert=True,
            )
