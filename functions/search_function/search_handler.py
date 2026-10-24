import html

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from database.files_database.files_db import format_file_size, search_files


def register_search_handler(bot: AsyncTeleBot) -> None:
    """Registers the /search command handler on the bot."""

    @bot.message_handler(commands=["search"])
    async def handle_search(message: Message) -> None:
        if not message.from_user:
            return

        parts = (message.text or "").split(None, 1)
        query = parts[1].strip() if len(parts) > 1 else ""
        if not query:
            await bot.reply_to(
                message,
                "<b>Usage:</b> <code>/search &lt;query&gt;</code>",
                parse_mode="HTML",
            )
            return

        results, total_count = await search_files(query=query, limit=5, skip=0)
        if not results:
            await bot.reply_to(
                message,
                f"❌ No files found for <b>{html.escape(query)}</b>.",
                parse_mode="HTML",
            )
            return

        lines = []
        for index, item in enumerate(results[:5], start=1):
            file_name = str(item.get("file_name") or "Unknown file")
            file_type = str(item.get("file_type") or "ebook").upper()
            file_size = format_file_size(item.get("file_size"))
            lines.append(
                f"{index}. <b>{html.escape(file_name)}</b>\n"
                f"   {file_type} • {file_size}"
            )

        response = (
            f"<b>🔎 Search results for:</b> <code>{html.escape(query)}</code>\n\n"
            + "\n\n".join(lines)
        )
        if total_count > len(results):
            response += f"\n\n<i>Showing {len(results)} of {total_count} results.</i>"

        await bot.reply_to(message, response, parse_mode="HTML")


__all__ = ["register_search_handler"]
