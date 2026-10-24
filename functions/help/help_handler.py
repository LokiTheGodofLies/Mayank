import html

from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import config.settings as settings
from config.strings import SCRIPT_KEYS_ORDER, SCRIPT_TITLES
from database.scripts_database.scripts_db import (
    add_script_button_row,
    add_script_media,
    clear_script_buttons,
    clear_script_media,
    get_script_config,
    reset_script_to_default,
    update_script_text,
)
from functions.permissions import is_admin_or_owner, require_admin_or_owner
from functions.script_engine.script_sender import send_script_message

PAGE_SIZE = 10
ACTIVE_EDIT_SESSIONS: dict[int, dict[str, str]] = {}


def build_script_page_markup(page: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    total_pages = max(1, (len(SCRIPT_KEYS_ORDER) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, total_pages))

    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    for script_key in SCRIPT_KEYS_ORDER[start:end]:
        title = SCRIPT_TITLES.get(script_key, script_key.title())
        markup.row(
            InlineKeyboardButton(
                text=title,
                callback_data=f"es:open:{script_key}",
            )
        )

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Prev", callback_data=f"es:page:{page - 1}")
        )
    nav_buttons.append(
        InlineKeyboardButton(f"{page}/{total_pages}", callback_data="es:noop")
    )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"es:page:{page + 1}")
        )
    markup.row(*nav_buttons)
    return markup


def build_script_editor_markup(script_key: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🖼 Media", callback_data=f"es:media:{script_key}"),
        InlineKeyboardButton("✏️ Text", callback_data=f"es:text:{script_key}"),
    )
    markup.row(
        InlineKeyboardButton("🔘 Buttons", callback_data=f"es:buttons:{script_key}"),
        InlineKeyboardButton("👀 Preview", callback_data=f"es:preview:{script_key}"),
    )
    markup.row(
        InlineKeyboardButton("↩️ Reset Default", callback_data=f"es:reset:{script_key}"),
        InlineKeyboardButton("⬅️ Back", callback_data=f"es:page:1"),
    )
    return markup


def build_media_menu(script_key: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("➕ Add Media", callback_data=f"es:media_add:{script_key}"),
        InlineKeyboardButton("🗑 Clear Pool", callback_data=f"es:media_clear:{script_key}"),
    )
    markup.row(
        InlineKeyboardButton("⬅️ Back", callback_data=f"es:open:{script_key}"),
    )
    return markup


def build_button_menu(script_key: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("➕ Add Button Row", callback_data=f"es:buttons_add:{script_key}"),
        InlineKeyboardButton("🗑 Clear Buttons", callback_data=f"es:buttons_clear:{script_key}"),
    )
    markup.row(
        InlineKeyboardButton("⬅️ Back", callback_data=f"es:open:{script_key}"),
    )
    return markup


async def show_script_list(bot: AsyncTeleBot, chat_id: int, page: int = 1) -> None:
    page = max(1, page)
    text = "<b>🧩 /editscript — Bot Script Manager</b>\n\nSelect a script to customize."
    markup = build_script_page_markup(page)
    await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)


async def open_script_editor(bot: AsyncTeleBot, call: CallbackQuery, script_key: str) -> None:
    title = SCRIPT_TITLES.get(script_key, script_key.title())
    config = await get_script_config(script_key)
    preview = (config.get("text") or "")
    preview = html.escape(preview)[:250]
    text = (
        f"<b>{title}</b>\n\n"
        f"<i>Script Key:</i> <code>{html.escape(script_key)}</code>\n\n"
        f"<i>Preview:</i>\n{preview or '<i>No custom text yet.</i>'}"
    )
    await bot.edit_message_text(
        text=text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="HTML",
        reply_markup=build_script_editor_markup(script_key),
    )


async def handle_text_edit(bot: AsyncTeleBot, message: Message, script_key: str) -> None:
    new_text = (message.text or message.caption or "").strip()
    if not new_text:
        await bot.reply_to(message, "Please send the new script text.")
        return

    ok = await update_script_text(script_key, new_text, parse_mode="HTML")
    if ok:
        await bot.reply_to(
            message,
            f"✅ Saved custom text for <code>{html.escape(script_key)}</code>.",
            parse_mode="HTML",
        )
    else:
        await bot.reply_to(message, "Failed to save the text.")

    ACTIVE_EDIT_SESSIONS.pop(message.from_user.id, None)


async def handle_media_add(bot: AsyncTeleBot, message: Message, script_key: str) -> None:
    file_id = None
    media_type = None
    duration = None

    if getattr(message, "photo", None):
        file_id = message.photo[-1].file_id
        media_type = "photo"
    elif getattr(message, "animation", None):
        file_id = message.animation.file_id
        media_type = "animation"
        duration = getattr(message.animation, "duration", None)
    elif getattr(message, "video", None):
        file_id = message.video.file_id
        media_type = "video"
        duration = getattr(message.video, "duration", None)
    else:
        await bot.reply_to(message, "Please send a photo, GIF, or short video (<= 10 seconds).")
        return

    if media_type == "video" and duration is not None and duration > 10:
        await bot.reply_to(
            message,
            "🚫 Video too long. Please send a video of 10 seconds or less.",
            parse_mode="HTML",
        )
        return

    ok, response = await add_script_media(
        script_key=script_key,
        file_id=file_id,
        file_unique_id=f"{script_key}:{file_id}",
        media_type=media_type,
        duration=duration,
    )

    if ok:
        await bot.reply_to(message, response)
    else:
        await bot.reply_to(message, response)

    ACTIVE_EDIT_SESSIONS.pop(message.from_user.id, None)


async def handle_button_input(bot: AsyncTeleBot, message: Message, script_key: str) -> None:
    payload = (message.text or "").strip()
    if not payload:
        await bot.reply_to(message, "Please send button data in this format:\n<code>Label|url|https://example.com</code>\nor\n<code>Label|cmd|cmd:start</code>", parse_mode="HTML")
        return

    parts = [p.strip() for p in payload.split("|")]
    if len(parts) < 3:
        await bot.reply_to(message, "Invalid format. Use: <code>Label|url|https://example.com</code>", parse_mode="HTML")
        return

    label, button_type, value = parts[0], parts[1].lower(), "|".join(parts[2:])
    if button_type not in {"url", "cmd"}:
        await bot.reply_to(message, "Button type must be <code>url</code> or <code>cmd</code>.", parse_mode="HTML")
        return

    button_row = [{"text": label, "type": button_type, "value": value}]
    await add_script_button_row(script_key, button_row)
    await bot.reply_to(message, f"✅ Added button row to <code>{html.escape(script_key)}</code>.", parse_mode="HTML")
    ACTIVE_EDIT_SESSIONS.pop(message.from_user.id, None)


async def send_script_preview(bot: AsyncTeleBot, call: CallbackQuery, script_key: str) -> None:
    await send_script_message(
        bot,
        chat_id=call.message.chat.id,
        script_key=script_key,
        context={
            "user_name": call.from_user.first_name if call.from_user else "User",
            "username": call.from_user.username or "unknown",
            "user_id": call.from_user.id if call.from_user else 0,
            "user_link": f"tg://user?id={call.from_user.id}" if call.from_user else "",
            "user_role": "owner" if settings.is_owner(call.from_user.id) else "admin",
            "bot_name": "Mayank Bot",
            "bot_username": "MayankBot",
            "bot_link": "https://t.me/MayankBot",
            "file_name": "Sample Book.epub",
            "file_size": "12 MB",
            "file_id": "sample_file_id",
            "duration": "01:20",
            "caption": "Preview caption",
            "extension": "epub",
            "file_type": "ebook",
            "delete_minutes": "5",
            "query": "Atomic Habits",
            "total": "12",
            "page": "1",
            "total_pages": "2",
            "fetched": "90",
            "remaining": "15",
            "forwarded": "75",
            "duplicate": "5",
            "deleted": "3",
            "skipped": "7",
            "filtered": "4",
            "status": "preview",
            "percentage": "80",
            "footer": "preview",
            "chat_title": call.message.chat.title or "Preview Chat",
            "chat_id": call.message.chat.id,
            "chat_username": call.message.chat.username or "previewchat",
            "invite_link": "https://t.me/previewchat",
            "topic_id": call.message.message_thread_id,
            "permissions": "Administrator",
            "action": "Preview",
            "date_time": "Preview Time",
        },
    )


def register_editscript_handler(bot: AsyncTeleBot) -> None:
    @bot.message_handler(commands=["editscript"])
    async def handle_editscript_command(message: Message):
        if not await require_admin_or_owner(bot, message):
            return
        await show_script_list(bot, message.chat.id, 1)

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("es:"))
    async def handle_editscript_callback(call: CallbackQuery):
        if not call.from_user or not is_admin_or_owner(call.from_user.id):
            await bot.answer_callback_query(call.id, "Access denied.", show_alert=True)
            return

        data = call.data or ""
        if data == "es:noop":
            await bot.answer_callback_query(call.id)
            return

        parts = data.split(":")
        action = parts[1] if len(parts) > 1 else ""

        if action == "page":
            page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
            await bot.edit_message_text(
                text="<b>🧩 /editscript — Bot Script Manager</b>\n\nSelect a script to customize.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=build_script_page_markup(page),
            )
            await bot.answer_callback_query(call.id)
            return

        if action == "open":
            script_key = parts[2] if len(parts) > 2 else None
            if script_key:
                await open_script_editor(bot, call, script_key)
            await bot.answer_callback_query(call.id)
            return

        if action == "media":
            script_key = parts[2] if len(parts) > 2 else None
            if script_key:
                await bot.edit_message_text(
                    text=f"<b>🖼 Media Manager</b>\n\nFor <code>{html.escape(script_key)}</code>.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    parse_mode="HTML",
                    reply_markup=build_media_menu(script_key),
                )
            await bot.answer_callback_query(call.id)
            return

        if action == "text":
            script_key = parts[2] if len(parts) > 2 else None
            if script_key:
                ACTIVE_EDIT_SESSIONS[call.from_user.id] = {"type": "text", "script_key": script_key}
                await bot.answer_callback_query(call.id, f"Send the new text for {script_key}.")
                await bot.edit_message_text(
                    text=f"<b>✏️ Edit Script Text</b>\n\nSend the new text for <code>{html.escape(script_key)}</code>.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    parse_mode="HTML",
                    reply_markup=build_script_editor_markup(script_key),
                )
            return

        if action == "buttons":
            script_key = parts[2] if len(parts) > 2 else None
            if script_key:
                await bot.edit_message_text(
                    text=f"<b>🔘 Button Manager</b>\n\nFor <code>{html.escape(script_key)}</code>.\n\nFormat: <code>Label|url|https://example.com</code> or <code>Label|cmd|cmd:start</code>",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    parse_mode="HTML",
                    reply_markup=build_button_menu(script_key),
                )
            await bot.answer_callback_query(call.id)
            return

        if action == "preview":
            script_key = parts[2] if len(parts) > 2 else None
            if script_key:
                await send_script_preview(bot, call, script_key)
            await bot.answer_callback_query(call.id, "Preview sent.")
            return

        if action == "reset":
            script_key = parts[2] if len(parts) > 2 else None
            if script_key:
                await reset_script_to_default(script_key)
                await bot.answer_callback_query(call.id, f"Reset {script_key} to default.", show_alert=True)
                await open_script_editor(bot, call, script_key)
            return

        if action == "media_add":
            script_key = parts[2] if len(parts) > 2 else None
            if script_key:
                ACTIVE_EDIT_SESSIONS[call.from_user.id] = {"type": "media", "script_key": script_key}
                await bot.answer_callback_query(call.id, "Send a photo, GIF, or short video to add to this script.")
                await bot.edit_message_text(
                    text=f"<b>🖼 Add Media</b>\n\nSend a photo, GIF, or video (<=10s) for <code>{html.escape(script_key)}</code>.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    parse_mode="HTML",
                    reply_markup=build_media_menu(script_key),
                )
            return

        if action == "media_clear":
            script_key = parts[2] if len(parts) > 2 else None
            if script_key:
                await clear_script_media(script_key)
                await bot.answer_callback_query(call.id, f"Cleared media pool for {script_key}.", show_alert=True)
                await open_script_editor(bot, call, script_key)
            return

        if action == "buttons_add":
            script_key = parts[2] if len(parts) > 2 else None
            if script_key:
                ACTIVE_EDIT_SESSIONS[call.from_user.id] = {"type": "buttons", "script_key": script_key}
                await bot.answer_callback_query(call.id, "Send button data in the format Label|url|https://... or Label|cmd|cmd:start")
                await bot.edit_message_text(
                    text=f"<b>🔘 Add Button Row</b>\n\nSend one row in the format:<code>Label|url|https://example.com</code> or <code>Label|cmd|cmd:start</code>.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    parse_mode="HTML",
                    reply_markup=build_button_menu(script_key),
                )
            return

        if action == "buttons_clear":
            script_key = parts[2] if len(parts) > 2 else None
            if script_key:
                await clear_script_buttons(script_key)
                await bot.answer_callback_query(call.id, f"Cleared buttons for {script_key}.", show_alert=True)
                await open_script_editor(bot, call, script_key)
            return

        if action == "back":
            page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
            await show_script_list(bot, call.message.chat.id, page)
            await bot.answer_callback_query(call.id)
            return

    @bot.message_handler(
        func=lambda message: message.from_user is not None and message.from_user.id in ACTIVE_EDIT_SESSIONS
    )
    async def handle_script_edit_input(message: Message):
        user_id = message.from_user.id
        session = ACTIVE_EDIT_SESSIONS.get(user_id)
        if not session:
            return

        if not is_admin_or_owner(user_id):
            await bot.reply_to(message, "🚫 You are not authorised. Only admins and owners can access this.")
            ACTIVE_EDIT_SESSIONS.pop(user_id, None)
            return

        session_type = session.get("type")
        script_key = session.get("script_key")
        if not script_key:
            ACTIVE_EDIT_SESSIONS.pop(user_id, None)
            return

        if session_type == "text":
            await handle_text_edit(bot, message, script_key)
            return

        if session_type == "media":
            await handle_media_add(bot, message, script_key)
            return

        if session_type == "buttons":
            await handle_button_input(bot, message, script_key)
            return


__all__ = ["register_editscript_handler"]
