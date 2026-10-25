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
        InlineKeyboardButton("🖼️ Media", callback_data=f"es:media:{script_key}"),
        InlineKeyboardButton("✏️ Text", callback_data=f"es:text:{script_key}"),
    )
    markup.row(
        InlineKeyboardButton("🔘 Buttons", callback_data=f"es:buttons:{script_key}"),
        InlineKeyboardButton("👀 Preview", callback_data=f"es:preview:{script_key}"),
    )
    markup.row(
        InlineKeyboardButton("🔄 Reset Default", callback_data=f"es:reset:{script_key}"),
        InlineKeyboardButton("⬅️ Back", callback_data="es:page:1"),
    )
    return markup


def build_media_menu(script_key: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("➕ Add Media", callback_data=f"es:media_add:{script_key}"),
        InlineKeyboardButton("🗑️ Clear Pool", callback_data=f"es:media_clear:{script_key}"),
    )
    markup.row(
        InlineKeyboardButton("⬅️ Back", callback_data=f"es:open:{script_key}"),
    )
    return markup


def build_button_menu(script_key: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("➕ Add Button Row", callback_data=f"es:buttons_add:{script_key}"),
        InlineKeyboardButton("🗑️ Clear Buttons", callback_data=f"es:buttons_clear:{script_key}"),
    )
    markup.row(
        InlineKeyboardButton("⬅️ Back", callback_data=f"es:open:{script_key}"),
    )
    return markup


async def show_script_list(bot: AsyncTeleBot, chat_id: int, page: int = 1) -> None:
    page = max(1, page)
    text = "<b>🧩 /editscript – Bot Script Manager</b>\n\nSelect a script to customize."
    markup = build_script_page_markup(page)
    await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)


async def open_script_editor(bot: AsyncTeleBot, call: CallbackQuery, script_key: str) -> None:
    title = SCRIPT_TITLES.get(script_key, script_key.title())
    config = await get_script_config(script_key)
    preview = config.get("text") or ""
    preview = html.escape(preview)[:250]
    text = (
        f"<b>{title}</b>\n\n"
        f"<i>Script Key:</i> <code>{html.escape(script_key)}</code>\n\n"
        f"<b>Current Text Preview:</b>\n<i>{preview}</i>\n\n"
        f"<b>Media Count:</b> {len(config.get('media_pool', []))}\n"
        f"<b>Button Rows:</b> {len(config.get('buttons', []))}"
    )
    markup = build_script_editor_markup(script_key)
    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=markup,
    )


async def handle_editscript_callback(bot: AsyncTeleBot, call: CallbackQuery) -> None:
    if not await is_admin_or_owner(call.from_user.id):
        await bot.answer_callback_query(call.id, "❌ Access denied.", show_alert=True)
        return

    data = call.data or ""
    parts = data.split(":")
    if len(parts) < 2:
        return

    action = parts[1]

    if action == "noop":
        await bot.answer_callback_query(call.id)
        return

    if action == "page":
        page = int(parts[2]) if len(parts) > 2 else 1
        markup = build_script_page_markup(page)
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="<b>🧩 /editscript – Bot Script Manager</b>\n\nSelect a script to customize.",
            parse_mode="HTML",
            reply_markup=markup,
        )
        return

    if action == "open":
        script_key = parts[2]
        await open_script_editor(bot, call, script_key)
        return

    if action == "media":
        script_key = parts[2]
        markup = build_media_menu(script_key)
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"<b>🖼️ Media Management</b>\n\nScript: <code>{html.escape(script_key)}</code>",
            parse_mode="HTML",
            reply_markup=markup,
        )
        return

    if action == "media_add":
        script_key = parts[2]
        ACTIVE_EDIT_SESSIONS[call.from_user.id] = {
            "mode": "add_media",
            "script_key": script_key,
        }
        await bot.send_message(
            call.message.chat.id,
            f"Send photo or video to add to pool for <code>{html.escape(script_key)}</code> (or send /cancel to abort).",
            parse_mode="HTML",
        )
        return

    if action == "media_clear":
        script_key = parts[2]
        await clear_script_media(script_key)
        await bot.answer_callback_query(call.id, "Cleared media pool.")
        await open_script_editor(bot, call, script_key)
        return

    if action == "text":
        script_key = parts[2]
        ACTIVE_EDIT_SESSIONS[call.from_user.id] = {
            "mode": "set_text",
            "script_key": script_key,
        }
        await bot.send_message(
            call.message.chat.id,
            f"Send new text for <code>{html.escape(script_key)}</code> (or send /cancel to abort).",
            parse_mode="HTML",
        )
        return

    if action == "buttons":
        script_key = parts[2]
        markup = build_button_menu(script_key)
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"<b>🔘 Buttons Management</b>\n\nScript: <code>{html.escape(script_key)}</code>",
            parse_mode="HTML",
            reply_markup=markup,
        )
        return

    if action == "buttons_add":
        script_key = parts[2]
        ACTIVE_EDIT_SESSIONS[call.from_user.id] = {
            "mode": "add_button_row",
            "script_key": script_key,
        }
        await bot.send_message(
            call.message.chat.id,
            "Send buttons in format: <code>Text1 | https://example.com || Text2 | callback_data</code> (or /cancel).",
            parse_mode="HTML",
        )
        return

    if action == "buttons_clear":
        script_key = parts[2]
        await clear_script_buttons(script_key)
        await bot.answer_callback_query(call.id, "Cleared buttons.")
        await open_script_editor(bot, call, script_key)
        return

    if action == "preview":
        script_key = parts[2]
        await send_script_message(bot, call.message.chat.id, script_key)
        await bot.answer_callback_query(call.id, "Preview sent.")
        return

    if action == "reset":
        script_key = parts[2]
        await reset_script_to_default(script_key)
        await bot.answer_callback_query(call.id, "Reset script to default.")
        await open_script_editor(bot, call, script_key)
        return


async def handle_text_input(bot: AsyncTeleBot, message: Message) -> bool:
    if not message.from_user:
        return False

    session = ACTIVE_EDIT_SESSIONS.get(message.from_user.id)
    if not session:
        return False

    if message.text and message.text.strip().lower() == "/cancel":
        ACTIVE_EDIT_SESSIONS.pop(message.from_user.id, None)
        await bot.reply_to(message, "❎ Cancelled script edit session.")
        return True

    mode = session.get("mode")
    script_key = session.get("script_key")
    if not script_key:
        return False

    if mode == "set_text":
        if not message.text:
            return False
        await update_script_text(script_key, message.text)
        ACTIVE_EDIT_SESSIONS.pop(message.from_user.id, None)
        await bot.reply_to(
            message,
            f"✅ Text updated for <code>{html.escape(script_key)}</code>",
            parse_mode="HTML",
        )
        return True

    if mode == "add_button_row":
        if not message.text:
            return False
        row = []
        raw_buttons = message.text.split("||")
        for btn in raw_buttons:
            if "|" in btn:
                t, u = btn.split("|", 1)
                val = u.strip()
                btn_type = "url" if val.startswith(("http://", "https://", "tg://")) else "callback"
                row.append({"text": t.strip(), "type": btn_type, "value": val})
        if row:
            await add_script_button_row(script_key, row)
            ACTIVE_EDIT_SESSIONS.pop(message.from_user.id, None)
            await bot.reply_to(
                message,
                f"✅ Added button row for <code>{html.escape(script_key)}</code>",
                parse_mode="HTML",
            )
        else:
            await bot.reply_to(message, "❌ Invalid format. Use: <code>Text | URL</code>", parse_mode="HTML")
        return True

    return False


async def handle_media_input(bot: AsyncTeleBot, message: Message) -> bool:
    if not message.from_user:
        return False

    session = ACTIVE_EDIT_SESSIONS.get(message.from_user.id)
    if not session or session.get("mode") != "add_media":
        return False

    script_key = session.get("script_key")
    if not script_key:
        return False

    file_id = None
    file_unique_id = None
    media_type = None
    duration = None

    if message.photo:
        file_id = message.photo[-1].file_id
        file_unique_id = message.photo[-1].file_unique_id
        media_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_unique_id = message.video.file_unique_id
        media_type = "video"
        duration = getattr(message.video, "duration", None)

    if file_id and file_unique_id and media_type:
        ok, resp_msg = await add_script_media(
            script_key=script_key,
            file_id=file_id,
            file_unique_id=file_unique_id,
            media_type=media_type,
            duration=duration,
        )
        ACTIVE_EDIT_SESSIONS.pop(message.from_user.id, None)
        await bot.reply_to(
            message,
            resp_msg if ok else f"❌ {html.escape(str(resp_msg))}",
            parse_mode="HTML",
        )
        return True

    return False


def register_help_handler(bot: AsyncTeleBot) -> None:
    """Registers /help, /editscript, callback handlers, and active session listeners."""

    @bot.message_handler(commands=["help"])
    async def _help_cmd(message: Message) -> None:
        user_name = html.escape(message.from_user.first_name or "User") if message.from_user else "User"
        await send_script_message(
            bot,
            message.chat.id,
            "help_menu",
            context={"first_name": user_name, "user_id": getattr(message.from_user, "id", "")},
        )

    @bot.message_handler(commands=["editscript"])
    @require_admin_or_owner
    async def _editscript_cmd(message: Message) -> None:
        await show_script_list(bot, message.chat.id, page=1)

    @bot.callback_query_handler(func=lambda c: bool(c.data and c.data.startswith("es:")))
    async def _editscript_cb(call: CallbackQuery) -> None:
        await handle_editscript_callback(bot, call)

    @bot.message_handler(
        content_types=["photo", "video"],
        func=lambda m: bool(m.from_user and m.from_user.id in ACTIVE_EDIT_SESSIONS),
    )
    async def _editscript_media_msg(message: Message) -> None:
        await handle_media_input(bot, message)

    @bot.message_handler(
        content_types=["text"],
        func=lambda m: bool(m.from_user and m.from_user.id in ACTIVE_EDIT_SESSIONS),
    )
    async def _editscript_text_msg(message: Message) -> None:
        await handle_text_input(bot, message)


# Alias for backward compatibility if any module imports register_editscript_handler
register_editscript_handler = register_help_handler

__all__ = ["register_help_handler", "register_editscript_handler"]
