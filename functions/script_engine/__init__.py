import asyncio

from telebot.async_telebot import AsyncTeleBot

import config.settings as settings
from database.config_database.config_db import get_all_config_vars
from database.files_database.files_db import init_files_db_indexes
from database.scripts_database.scripts_db import init_scripts_db_indexes
from functions.admin_config.redeploy_manager import register_redeploy_handler
from functions.admin_config.var_manager import register_var_manager_handler
from functions.chat_tracker.tracker_handler import register_chat_tracker_handler
from functions.error_logger.error_log_sender import verify_startup_configuration
from functions.indexer.indexer_handler import register_indexer_handler
from functions.script_engine.editscript_handler import register_editscript_handler
from functions.search_function.search_handler import register_search_handler
from functions.start_function.start_handler import register_start_handler
from server.web_server import start_web_server


async def main() -> None:
    # 1. Load dynamic configuration overrides from MongoDB
    try:
        overrides = await get_all_config_vars()
        if overrides:
            settings.apply_config_overrides(overrides)
            print("[INIT] Loaded configuration overrides from MongoDB.")
    except Exception as e:
        print(f"[INIT WARNING] Could not load config overrides: {e}")

    # 2. Ensure MongoDB indexes for indexed files and scripts
    await init_files_db_indexes()
    await init_scripts_db_indexes()

    if not settings.BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing! Please set it in .env or environment variables.")

    bot = AsyncTeleBot(settings.BOT_TOKEN)

    # 3. Register all bot handlers
    register_start_handler(bot)
    register_chat_tracker_handler(bot)
    register_redeploy_handler(bot)
    register_var_manager_handler(bot)
    register_indexer_handler(bot)
    register_search_handler(bot)
    register_editscript_handler(bot)

    # 4. Start the aiohttp web server for Render health checks
    await start_web_server()

    # 5. Verify startup configuration and send startup logs
    await verify_startup_configuration(bot)

    # 6. Clear existing webhooks and start infinity polling
    await bot.remove_webhook()
    print("[BOT] Starting Telegram Bot polling...")
    await bot.infinity_polling(
        allowed_updates=[
            "message",
            "edited_message",
            "channel_post",
            "edited_channel_post",
            "my_chat_member",
            "chat_member",
            "callback_query",
        ]
    )


if __name__ == "__main__":
    asyncio.run(main())
