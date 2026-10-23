from telebot.async_telebot import AsyncTeleBot
from telebot.types import ChatMemberUpdated
from database.channels_database.channels_db import save_channel
from database.groups_database.groups_db import save_group
from database.users_database.users_db import save_user
from functions.chat_tracker.chat_log_sender import send_chat_status_log


async def try_get_invite_link(bot: AsyncTeleBot, chat_id: int) -> str | None:
    """Attempts to fetch or export the chat invite link if the bot has admin permissions."""
    try:
        chat_info = await bot.get_chat(chat_id)
        if getattr(chat_info, "invite_link", None):
            return chat_info.invite_link
        return await bot.export_chat_invite_link(chat_id)
    except Exception:
        return None


def register_chat_tracker_handler(bot: AsyncTeleBot) -> None:
    """Registers the my_chat_member handler to track bot additions and removals."""

    @bot.my_chat_member_handler()
    async def handle_my_chat_member(update: ChatMemberUpdated) -> None:
        chat = update.chat
        if chat.type not in ("channel", "group", "supergroup"):
            return

        old_status = update.old_chat_member.status
        new_status = update.new_chat_member.status
        action_user = update.from_user

        # Save the user who performed the action if available
        if action_user and not action_user.is_bot:
            await save_user(
                user_id=action_user.id,
                full_name=action_user.full_name or "Unknown",
                username=action_user.username,
            )

        was_added = old_status in ("left", "kicked") and new_status in (
            "member",
            "administrator",
            "restricted",
        )
        was_removed = old_status in (
            "member",
            "administrator",
            "restricted",
        ) and new_status in ("left", "kicked")
        was_promoted = old_status == "member" and new_status == "administrator"

        if was_added or was_promoted:
            invite_link = None
            if new_status == "administrator":
                invite_link = await try_get_invite_link(bot, chat.id)

            if chat.type == "channel":
                record = await save_channel(
                    channel_id=chat.id,
                    channel_name=chat.title or "Unnamed Channel",
                    username=chat.username,
                    invite_link=invite_link,
                    status="active",
                )
            else:
                record = await save_group(
                    group_id=chat.id,
                    group_name=chat.title or "Unnamed Group",
                    username=chat.username,
                    invite_link=invite_link,
                    status="active",
                )

            if was_added:
                await send_chat_status_log(
                    bot=bot,
                    chat=chat,
                    action_user=action_user,
                    action="added",
                    invite_link=record.get("invite_link"),
                )

        elif was_removed:
            if chat.type == "channel":
                record = await save_channel(
                    channel_id=chat.id,
                    channel_name=chat.title or "Unnamed Channel",
                    username=chat.username,
                    status="removed",
                )
            else:
                record = await save_group(
                    group_id=chat.id,
                    group_name=chat.title or "Unnamed Group",
                    username=chat.username,
                    status="removed",
                )

            await send_chat_status_log(
                bot=bot,
                chat=chat,
                action_user=action_user,
                action="removed",
                invite_link=record.get("invite_link"),
            )
