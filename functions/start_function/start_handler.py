from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from database.users_database.users_db import save_user
from functions.start_function.user_log_sender import send_user_start_log


def register_start_handler(bot: AsyncTeleBot) -> None:
    """Registers the /start command handler on the bot."""

    @bot.message_handler(commands=["start"])
    async def handle_start(message: Message) -> None:
        user = message.from_user
        if user is None:
            return

        # 1. Save user and determine role (owner / admin / normal_user) in MongoDB
        user_record = await save_user(
            user_id=user.id,
            full_name=user.full_name or "Unknown",
            username=user.username,
        )
        role = user_record.get("role", "normal_user")

        # 2. Reply to the user
        await bot.reply_to(message, "hi I am just a telegram bot under test")

        # 3. Send log message to the User Logs forum topic
        await send_user_start_log(bot=bot, user=user, role=role)
