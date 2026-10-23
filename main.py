import asyncio
from telebot.async_telebot import AsyncTeleBot
from config.settings import BOT_TOKEN
from functions.start_function.start_handler import register_start_handler
from functions.chat_tracker.tracker_handler import register_chat_tracker_handler
from server.web_server import start_web_server


async def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing! Please set it in Render Environment Variables.")

    # Initialize the bot
    bot = AsyncTeleBot(BOT_TOKEN)

    # Register all modular function handlers
    register_start_handler(bot)
    register_chat_tracker_handler(bot)

    # Start the lightweight HTTP server for Render port binding
    await start_web_server()

    # Clear any existing webhook before polling
    await bot.remove_webhook()

    bot_info = await bot.get_me()
    print(f"[main] Bot @{bot_info.username} started and listening for updates...")

    # Start polling (explicitly including my_chat_member for group/channel add & remove logs)
    await bot.infinity_polling(
        allowed_updates=[
            "message",
            "edited_message",
            "channel_post",
            "edited_channel_post",
            "my_chat_member",
            "chat_member",
            "callback_query",
        ],
        skip_pending=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
