import html

from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

HELP_PAGES = {
    1: {
        "title": "User Commands",
        "commands": [
            ("/start", "Start the bot and save your profile."),
            ("/search <keyword>", "Search the indexed library for books or audiobooks."),
            ("/help", "Open this command help menu."),
        ],
    },
    2: {
        "title": "Admin Commands",
        "commands": [
            ("/index <chat_id> <last_msg_id> [skip_id] [topic_id]", "Index files from a source chat into the library."),
            ("/ban <user_id> [reason]", "Ban a user from using the bot."),
            ("/unban <user_id>", "Remove a user ban."),
            ("/getvars", "Display active config values and Mongo overrides."),
            ("/setvar KEY VALUE", "Set a runtime config value for the bot."),
            ("/delvar KEY", "Remove a MongoDB override for a config key."),
            ("/editscript", "Open the script editor and customize bot messages."),
        ],
    },
    3: {
        "title": "Owner Commands",
        "commands": [
            ("/editscript", "Customize the bot's script text, media, and buttons."),
            ("/setvar KEY VALUE", "Persist runtime config values in MongoDB for the live bot."),
            ("/delvar KEY", "Remove an override and restore the default environment value."),
            ("/restart", "Restart the Python bot process immediately."),
            ("/redeploy", "Trigger a Render redeploy using the configured webhook."),
            ("/ban <user_id> [reason]", "Owner/admin-level moderation action for disruptive users."),
        ],
    },
}


def build_help_markup(page: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    total_pages = len(HELP_PAGES)
    page = max(1, min(int(page), total_pages))

    for target_page in range(1, total_pages + 1):
        label = f"{target_page}"
        if target_page == page:
            label = f"● {target_page} ●"
        markup.add(
            InlineKeyboardButton(label, callback_data=f"help:page:{target_page}")
        )

    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"help:page:{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="help:noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"help:page:{page + 1}"))
    markup.row(*nav_row)
    return markup


def build_help_text(page: int) -> str:
    info = HELP_PAGES.get(page, HELP_PAGES[1])
    title = info["title"]
    lines = [f"<b>📘 {html.escape(title)}</b>", ""]

    for command, description in info["commands"]:
        lines.append(f"<b>{html.escape(command)}</b> — {html.escape(description)}")

    lines.append("")
    lines.append("<i>Use the buttons below to switch between command groups.</i>")
    return "\n".join(lines)


async def show_help_page(bot: AsyncTeleBot, chat_id: int, page: int = 1, *, message_id: int | None = None) -> None:
    page = max(1, min(int(page), len(HELP_PAGES)))
    text = build_help_text(page)
    markup = build_help_markup(page)

    if message_id is not None:
        await bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            parse_mode="HTML",
            reply_markup=markup,
        )
    else:
        await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)


def register_help_handler(bot: AsyncTeleBot) -> None:
    """Registers the /help command and the multi-page inline help menu."""

    @bot.message_handler(commands=["help"])
    async def handle_help_cmd(message: Message):
        await show_help_page(bot, message.chat.id, 1)

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("help:"))
    async def handle_help_callback(call: CallbackQuery):
        data = call.data or ""
        if data == "help:noop":
            await bot.answer_callback_query(call.id)
            return

        try:
            _, _, page_str = data.split(":")
            page = int(page_str)
        except (ValueError, TypeError):
            page = 1

        await show_help_page(bot, call.message.chat.id, page, message_id=call.message.message_id)
        await bot.answer_callback_query(call.id)


__all__ = ["register_help_handler", "build_help_text", "HELP_PAGES"]
