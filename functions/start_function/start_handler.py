import html
import random
import re
from typing import Any

from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.scripts_database.scripts_db import get_script_config


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def render_script_text(template: str, context: dict[str, Any] | None = None) -> str:
    """Replaces {placeholder} values inside a script template with escaped HTML-safe strings."""
    if not template:
        return ""
    context = context or {}

    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        value = context.get(key, "")
        return html.escape(_stringify(value), quote=False)

    return re.sub(r"\{([a-zA-Z0-9_]+)\}", replacer, template)


def build_script_keyboard(button_rows: list[list[dict]] | None) -> InlineKeyboardMarkup | None:
    """Builds an InlineKeyboardMarkup from rows stored in scripts_database."""
    rows = button_rows or []
    if not rows:
        return None

    markup = InlineKeyboardMarkup()
    for row in rows:
        if not row:
            continue

        buttons = []
        for button in row:
            text = _stringify(button.get("text") or "Button")
            button_type = str(button.get("type") or "callback").lower().strip()
            value = _stringify(button.get("value") or "")

            if button_type in {"url", "link"}:
                buttons.append(InlineKeyboardButton(text=text, url=value))
            elif button_type in {"command", "cmd", "callback"}:
                buttons.append(InlineKeyboardButton(text=text, callback_data=value or "cmd:start"))
            else:
                buttons.append(InlineKeyboardButton(text=text, callback_data=value or "noop"))

        markup.row(*buttons)
    return markup


async def send_script_message(
    bot: AsyncTeleBot,
    chat_id: int | str,
    script_key: str,
    context: dict[str, Any] | None = None,
    *,
    reply_to_message_id: int | None = None,
    message_thread_id: int | None = None,
    parse_mode: str | None = None,
    allow_media: bool = True,
) -> Any:
    """
    Renders a stored script, applies placeholders, optionally selects a random media item,
    attaches custom inline buttons, and sends it to the target chat.
    """
    script = await get_script_config(script_key)
    template = script.get("text") or ""
    text = render_script_text(template, context)

    keyboard = build_script_keyboard(script.get("buttons") or [])
    media_pool = script.get("media_pool") or []
    chosen_media = random.choice(media_pool) if allow_media and media_pool else None

    send_kwargs: dict[str, Any] = {"chat_id": chat_id}
    if parse_mode is None:
        parse_mode = script.get("parse_mode") or "HTML"
    send_kwargs["parse_mode"] = parse_mode
    if keyboard is not None:
        send_kwargs["reply_markup"] = keyboard
    if reply_to_message_id is not None:
        send_kwargs["reply_to_message_id"] = reply_to_message_id
    if message_thread_id is not None:
        send_kwargs["message_thread_id"] = message_thread_id

    if chosen_media:
        media_type = str(chosen_media.get("media_type") or "photo").lower()
        file_id = chosen_media.get("file_id")
        if not file_id:
            return await bot.send_message(text=text, **send_kwargs)

        send_kwargs["caption"] = text
        send_kwargs["disable_web_page_preview"] = True

        if media_type == "photo":
            return await bot.send_photo(photo=file_id, **send_kwargs)
        if media_type == "animation":
            return await bot.send_animation(animation=file_id, **send_kwargs)
        if media_type == "video":
            return await bot.send_video(video=file_id, **send_kwargs)

    return await bot.send_message(text=text, **send_kwargs)


async def send_script_reply(
    bot: AsyncTeleBot,
    message: Any,
    script_key: str,
    context: dict[str, Any] | None = None,
    *,
    allow_media: bool = True,
) -> Any:
    """Convenience wrapper that sends a script in reply to an existing Telegram message."""
    return await send_script_message(
        bot,
        chat_id=message.chat.id,
        script_key=script_key,
        context=context,
        reply_to_message_id=message.message_id,
        allow_media=allow_media,
    )


__all__ = [
    "render_script_text",
    "build_script_keyboard",
    "send_script_message",
    "send_script_reply",
]
