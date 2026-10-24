import html
import re
from typing import Any

from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.users_database.users_db import save_user
from functions.script_engine.script_sender import send_script_message
from functions.start_function.user_log_sender import send_user_start_log


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


def register_start_handler(bot: AsyncTeleBot) -> None:
    """Registers the /start command handler on the bot."""

    @bot.message_handler(commands=["start"])
    async def handle_start(message: Message) -> None:
        user = message.from_user
        if user is None:
            return

        user_record = await save_user(
            user_id=user.id,
            full_name=user.full_name or "Unknown",
            username=user.username,
        )
        role = user_record.get("role", "normal_user")

        bot_info = await bot.get_me()
        await send_script_message(
            bot,
            chat_id=message.chat.id,
            script_key="start",
            context={
                "user_name": user.full_name or "User",
                "username": user.username or "",
                "user_id": user.id,
                "user_link": f"tg://user?id={user.id}",
                "user_role": role,
                "bot_name": bot_info.first_name or "Bot",
                "bot_username": bot_info.username or "",
                "bot_link": f"https://t.me/{bot_info.username}" if bot_info.username else "",
            },
        )

        await send_user_start_log(bot=bot, user=user, role=role)


__all__ = [
    "_stringify",
    "render_script_text",
    "build_script_keyboard",
    "register_start_handler",
]
