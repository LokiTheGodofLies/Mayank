from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from database.users_database.users_db import save_user
from functions.script_engine.script_sender import send_script_message
from functions.start_function.user_log_sender import send_user_start_log


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
                "bot_name": (await bot.get_me()).first_name or "Bot",
                "bot_username": (await bot.get_me()).username or "",
                "bot_link": f"https://t.me/{(await bot.get_me()).username}",
            },
        )

        await send_user_start_log(bot=bot, user=user, role=role)
