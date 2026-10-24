import asyncio
import os
import sys
import aiohttp
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message


async def process_restart(bot: AsyncTeleBot, message: Message) -> None:
    """Restarts the Python bot process immediately (~2 seconds) to reload all variables."""
    await bot.reply_to(
        message,
        "🔄 <b>Restarting bot process...</b>\n"
        "All saved MongoDB and Render variables will be reloaded in a few seconds.",
        parse_mode="HTML",
    )
    await asyncio.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)


async def process_redeploy(bot: AsyncTeleBot, message: Message) -> None:
    """Triggers a full Render cloud rebuild using RENDER_DEPLOY_HOOK_URL."""
    deploy_hook_url = os.getenv("RENDER_DEPLOY_HOOK_URL", "").strip()

    if not deploy_hook_url:
        await bot.reply_to(
            message,
            "⚠️ <b>RENDER_DEPLOY_HOOK_URL is not set yet.</b>\n\n"
            "To enable full Render cloud redeployments:\n"
            "1. Go to Render Dashboard → <b>Settings</b> → <b>Deploy Hook</b> and copy the URL.\n"
            "2. Send:\n<code>/setvar RENDER_DEPLOY_HOOK_URL your_copied_url</code>\n\n"
            "<i>Tip: If you only changed a variable via /setvar, just use /restart (takes 2 seconds)!</i>",
            parse_mode="HTML",
        )
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(deploy_hook_url) as resp:
                if resp.status in (200, 201, 202):
                    await bot.reply_to(
                        message,
                        "🚀 <b>Render Redeploy Triggered!</b>\n"
                        "Render is now pulling the latest code from GitHub and rebuilding your service.",
                        parse_mode="HTML",
                    )
                else:
                    body = await resp.text()
                    await bot.reply_to(
                        message,
                        f"❌ Render Deploy Hook returned status <code>{resp.status}</code>:\n"
                        f"<code>{body[:300]}</code>",
                        parse_mode="HTML",
                    )
    except Exception as e:
        await bot.reply_to(
            message,
            f"❌ Failed to trigger Render redeploy:\n<code>{e}</code>",
            parse_mode="HTML",
        )
