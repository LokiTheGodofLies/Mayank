import html
import os
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
import config.settings as settings
from database.config_database.config_db import (
    set_config_var,
    get_all_config_vars,
    delete_config_var,
)

# Keys that are displayed when running /getvars
TRACKED_KEYS = [
    "API_ID",
    "OWNER_IDS",
    "ADMIN_IDS",
    "LOG_GROUP_ID",
    "USER_LOG_TOPIC_ID",
    "GROUP_LOG_TOPIC_ID",
    "CHANNEL_LOG_TOPIC_ID",
    "DATABASE_NAME",
    "RENDER_DEPLOY_HOOK_URL",
]


async def process_setvar(bot: AsyncTeleBot, message: Message) -> None:
    """Handles /setvar KEY VALUE to update an environment variable and save it in MongoDB."""
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await bot.reply_to(
            message,
            "<b>Usage:</b> <code>/setvar KEY VALUE</code>\n"
            "<b>Example:</b> <code>/setvar USER_LOG_TOPIC_ID 12</code>",
            parse_mode="HTML",
        )
        return

    key = parts[1].strip().upper()
    value = parts[2].strip()

    await set_config_var(key, value)
    settings.apply_config_overrides({key: value})

    await bot.reply_to(
        message,
        f"✅ Variable <code>{html.escape(key)}</code> updated to:\n"
        f"<code>{html.escape(value)}</code>\n\n"
        f"<i>Saved in MongoDB. Use /restart to apply across all modules immediately.</i>",
        parse_mode="HTML",
    )


async def process_getvars(bot: AsyncTeleBot, message: Message) -> None:
    """Handles /getvars to list active configuration variables and MongoDB overrides."""
    db_overrides = await get_all_config_vars()
    all_keys = list(dict.fromkeys(TRACKED_KEYS + list(db_overrides.keys())))

    lines = ["<b>⚙️ Current Bot Variables:</b>\n"]
    for key in all_keys:
        val = os.getenv(key, "")
        source = "MongoDB Override" if key in db_overrides else "Render Env"
        # Mask sensitive keys if someone checks them in a group
        if key in ("BOT_TOKEN", "API_HASH", "MONGO_URL") and val:
            display_val = val[:6] + "..." + val[-4:]
        else:
            display_val = val if val else "Not Set"
        lines.append(
            f"• <b>{html.escape(key)}:</b> <code>{html.escape(display_val)}</code> <i>({source})</i>"
        )

    await bot.reply_to(message, "\n".join(lines), parse_mode="HTML")


async def process_delvar(bot: AsyncTeleBot, message: Message) -> None:
    """Handles /delvar KEY to remove a MongoDB override."""
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await bot.reply_to(
            message,
            "<b>Usage:</b> <code>/delvar KEY</code>\n"
            "<b>Example:</b> <code>/delvar USER_LOG_TOPIC_ID</code>",
            parse_mode="HTML",
        )
        return

    key = parts[1].strip().upper()
    deleted = await delete_config_var(key)
    if deleted:
        await bot.reply_to(
            message,
            f"🗑 Removed MongoDB override for <code>{html.escape(key)}</code>.\n"
            f"<i>Send /restart to revert to the default Render variable.</i>",
            parse_mode="HTML",
        )
    else:
        await bot.reply_to(
            message,
            f"ℹ️ No MongoDB override found for <code>{html.escape(key)}</code>.",
            parse_mode="HTML",
        )
