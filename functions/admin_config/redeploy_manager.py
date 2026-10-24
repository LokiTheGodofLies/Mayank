import asyncio
import html
import os
import sys
import aiohttp
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
import config.settings as settings
from functions.error_logger.error_log_sender import (
    send_deployment_log,
    send_missing_var_log,
    send_error_log,
)


def is_owner(user_id: int) -> bool:
    """Checks if the user ID belongs to a configured Bot Owner."""
    owner_ids = getattr(settings, "OWNER_IDS", []) or []
    return int(user_id) in [int(uid) for uid in owner_ids]


def format_owner_mention(message: Message) -> str:
    """Formats a clickable HTML mention of the Owner who triggered the action."""
    user = getattr(message, "from_user", None)
    if not user:
        return "Owner"
    name = html.escape(getattr(user, "full_name", None) or getattr(user, "first_name", "Owner"))
    return f'<a href="tg://user?id={user.id}">{name}</a> (<code>{user.id}</code>)'


async def process_restart(bot: AsyncTeleBot, message: Message) -> None:
    """Logs the restart to Topic 35, notifies the Owner, and restarts the Python process."""
    if not message.from_user or not is_owner(message.from_user.id):
        await bot.reply_to(
            message,
            "🚫 <b>Access Denied!</b> Only Bot Owners can run <code>/restart</code>.",
            parse_mode="HTML",
        )
        return

    owner_mention = format_owner_mention(message)
    await bot.reply_to(
        message,
        "🔄 <b>Restarting bot in 2 seconds...</b>",
        parse_mode="HTML",
    )

    await send_deployment_log(
        bot=bot,
        event_type="Manual Process Restart (/restart)",
        status_text="Bot process is restarting via os.execv...",
        is_error=False,
        triggered_by=owner_mention,
    )

    await asyncio.sleep(2)
    os.execv(sys.executable, [sys.executable] + sys.argv)


async def process_redeploy(bot: AsyncTeleBot, message: Message) -> None:
    """Triggers a Render cloud rebuild via RENDER_DEPLOY_HOOK_URL and logs status to Topic 35."""
    if not message.from_user or not is_owner(message.from_user.id):
        await bot.reply_to(
            message,
            "🚫 <b>Access Denied!</b> Only Bot Owners can run <code>/redeploy</code>.",
            parse_mode="HTML",
        )
        return

    owner_mention = format_owner_mention(message)
    hook_url = (getattr(settings, "RENDER_DEPLOY_HOOK_URL", "") or "").strip()

    if not hook_url:
        await bot.reply_to(
            message,
            "⚠️ <b>RENDER_DEPLOY_HOOK_URL is not configured!</b>\n"
            "Set it using: <code>/setvar RENDER_DEPLOY_HOOK_URL &lt;url&gt;</code>",
            parse_mode="HTML",
        )
        await send_missing_var_log(
            bot=bot,
            missing_vars=["RENDER_DEPLOY_HOOK_URL"],
            context_action="/redeploy Command",
        )
        return

    status_msg = await bot.reply_to(
        message,
        "🚀 <b>Triggering Render cloud redeploy...</b>",
        parse_mode="HTML",
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(hook_url, timeout=15) as resp:
                resp_text = await resp.text()
                if resp.status in (200, 201, 202):
                    await bot.edit_message_text(
                        "✅ <b>Render redeploy triggered!</b>\n"
                        "Render is now building and deploying your latest commit.",
                        chat_id=status_msg.chat.id,
                        message_id=status_msg.message_id,
                        parse_mode="HTML",
                    )
                    await send_deployment_log(
                        bot=bot,
                        event_type="Render Cloud Redeploy (/redeploy)",
                        status_text=f"Webhook Accepted (HTTP {resp.status}) - New deployment started.",
                        is_error=False,
                        triggered_by=owner_mention,
                    )
                else:
                    await bot.edit_message_text(
                        f"❌ <b>Render redeploy failed!</b> (HTTP <code>{resp.status}</code>)",
                        chat_id=status_msg.chat.id,
                        message_id=status_msg.message_id,
                        parse_mode="HTML",
                    )
                    await send_deployment_log(
                        bot=bot,
                        event_type="Render Cloud Redeploy Failed (/redeploy)",
                        status_text=f"HTTP {resp.status}: {resp_text[:300]}",
                        is_error=True,
                        triggered_by=owner_mention,
                    )
    except Exception as e:
        await bot.edit_message_text(
            f"❌ <b>Error triggering Render webhook:</b> <code>{html.escape(str(e))}</code>",
            chat_id=status_msg.chat.id,
            message_id=status_msg.message_id,
            parse_mode="HTML",
        )
        await send_error_log(
            bot=bot,
            action="/redeploy Webhook Request",
            error=e,
            chat_title=getattr(message.chat, "title", "Private Chat"),
            chat_id=message.chat.id,
            user_name=getattr(message.from_user, "full_name", "Owner"),
            user_id=message.from_user.id,
        )


def register_redeploy_handler(bot: AsyncTeleBot) -> None:
    """Registers /restart and /redeploy commands for Bot Owners."""

    @bot.message_handler(commands=["restart"])
    async def handle_restart_cmd(message: Message):
        await process_restart(bot, message)

    @bot.message_handler(commands=["redeploy"])
    async def handle_redeploy_cmd(message: Message):
        await process_redeploy(bot, message)
