import html
import traceback
from datetime import datetime, timezone, timedelta
from telebot.async_telebot import AsyncTeleBot
import config.settings as settings


def get_ist_timestamp() -> str:
    """Returns current timestamp formatted in Indian Standard Time (IST, UTC+5:30)."""
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_tz).strftime("%Y-%m-%d %I:%M:%S %p IST")


async def _send_to_error_topic(bot: AsyncTeleBot, html_text: str) -> None:
    """Internal helper to send an HTML message to LOG_GROUP_ID under ERROR_LOG_TOPIC_ID (35)."""
    log_group_id = getattr(settings, "LOG_GROUP_ID", None)
    if not log_group_id:
        print(f"[ERROR_LOGGER] LOG_GROUP_ID not configured. Log text:\n{html_text}")
        return

    error_topic_id = getattr(settings, "ERROR_LOG_TOPIC_ID", 35)

    send_kwargs = {
        "chat_id": int(log_group_id),
        "text": html_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if error_topic_id:
        send_kwargs["message_thread_id"] = int(error_topic_id)

    try:
        await bot.send_message(**send_kwargs)
    except Exception as e:
        print(f"[ERROR_LOG_SENDER FAILED] Could not send to topic {error_topic_id}: {e}")


async def send_bot_not_admin_log(
    bot: AsyncTeleBot,
    chat_title: str,
    chat_id: int | str,
    missing_permission: str = "Administrator",
    action: str = "Indexing / Forwarding",
    chat_username: str | None = None,
) -> None:
    """
    Sends an alert to ERROR_LOG_TOPIC_ID (35) when the bot is not an admin
    or is missing a required permission in a channel or group.
    """
    safe_title = html.escape(str(chat_title or "Unknown Chat"))
    if chat_username:
        clean_u = html.escape(chat_username.lstrip("@"))
        chat_display = f'<a href="https://t.me/{clean_u}">{safe_title}</a> (@{clean_u})'
    else:
        chat_display = f"{safe_title} (<i>Private</i>)"

    timestamp = get_ist_timestamp()
    text = (
        f"⚠️ <b>#BOT_NOT_ADMIN_ERROR</b>\n\n"
        f"<b>• Action:</b> <code>{html.escape(action)}</code>\n"
        f"<b>• Chat Title:</b> {chat_display}\n"
        f"<b>• Chat ID:</b> <code>{chat_id}</code>\n"
        f"<b>• Missing Permission:</b> <code>{html.escape(missing_permission)}</code>\n"
        f"<b>• Fix:</b> Promote the bot to Administrator with the required permissions in this chat.\n"
        f"<b>• Time:</b> <code>{timestamp}</code>"
    )
    await _send_to_error_topic(bot, text)


async def send_missing_var_log(
    bot: AsyncTeleBot,
    missing_vars: list[str],
    context_action: str = "Configuration Check",
) -> None:
    """
    Sends an alert to ERROR_LOG_TOPIC_ID (35) when one or more required
    environment variables are missing or unconfigured.
    """
    if not missing_vars:
        return

    vars_joined = ", ".join(f"<code>{html.escape(v)}</code>" for v in missing_vars)
    fix_commands = "\n".join(f"<code>/setvar {html.escape(v)} &lt;value&gt;</code>" for v in missing_vars)
    timestamp = get_ist_timestamp()

    text = (
        f"⚠️ <b>#VARIABLE_MISSING_ERROR</b>\n\n"
        f"<b>• Context:</b> <code>{html.escape(context_action)}</code>\n"
        f"<b>• Missing Variables:</b> {vars_joined}\n\n"
        f"<b>• Quick Fix Command(s):</b>\n{fix_commands}\n\n"
        f"<b>• Time:</b> <code>{timestamp}</code>"
    )
    await _send_to_error_topic(bot, text)


async def send_deployment_log(
    bot: AsyncTeleBot,
    event_type: str,
    status_text: str,
    is_error: bool = False,
    triggered_by: str = "System / Render",
) -> None:
    """
    Sends Render startup, /restart, /redeploy, or deployment failure logs
    to ERROR_LOG_TOPIC_ID (35).
    """
    header = "🚨 <b>#RENDER_DEPLOY_ERROR</b>" if is_error else "🚀 <b>#RENDER_DEPLOYMENT_LOG</b>"
    timestamp = get_ist_timestamp()

    text = (
        f"{header}\n\n"
        f"<b>• Event:</b> <code>{html.escape(event_type)}</code>\n"
        f"<b>• Status:</b> <code>{html.escape(status_text)}</code>\n"
        f"<b>• Triggered By:</b> {triggered_by}\n"
        f"<b>• Time:</b> <code>{timestamp}</code>"
    )
    await _send_to_error_topic(bot, text)


async def send_error_log(
    bot: AsyncTeleBot,
    action: str,
    error: Exception | str,
    chat_title: str | None = None,
    chat_id: int | str | None = None,
    user_name: str | None = None,
    user_id: int | str | None = None,
) -> None:
    """
    Sends a general runtime/API/database exception report to ERROR_LOG_TOPIC_ID (35).
    """
    if isinstance(error, Exception):
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        raw_err = "".join(tb_lines[-3:]).strip()
    else:
        raw_err = str(error)

    if len(raw_err) > 1200:
        raw_err = raw_err[:1200] + "\n...[truncated]"

    chat_line = ""
    if chat_title or chat_id:
        c_title = html.escape(str(chat_title or "Unknown"))
        chat_line = f"<b>• Chat:</b> {c_title} (<code>{chat_id or 'N/A'}</code>)\n"

    user_line = ""
    if user_name or user_id:
        u_name = html.escape(str(user_name or "User"))
        if user_id:
            user_line = f'<b>• User:</b> <a href="tg://user?id={user_id}">{u_name}</a> (<code>{user_id}</code>)\n'
        else:
            user_line = f"<b>• User:</b> {u_name}\n"

    timestamp = get_ist_timestamp()
    text = (
        f"🚨 <b>#BOT_ERROR_LOG</b>\n\n"
        f"<b>• Context / Action:</b> <code>{html.escape(action)}</code>\n"
        f"{chat_line}"
        f"{user_line}"
        f"<b>• Error Details:</b>\n<pre>{html.escape(raw_err)}</pre>\n"
        f"<b>• Time:</b> <code>{timestamp}</code>"
    )
    await _send_to_error_topic(bot, text)


async def verify_startup_configuration(bot: AsyncTeleBot) -> None:
    """
    Runs on bot startup:
    1. Checks if any required environment variables are missing and logs them to Topic 35.
    2. Checks if the bot has Admin rights in INDEX_CHANNEL_ID and FILE_SHARING_CHANNEL_ID.
    3. Sends a Render Startup Status log to Topic 35.
    """
    required_vars = [
        "BOT_TOKEN",
        "MONGO_URL",
        "LOG_GROUP_ID",
        "USER_LOG_TOPIC_ID",
        "GROUP_LOG_TOPIC_ID",
        "CHANNEL_LOG_TOPIC_ID",
        "INDEX_LOG_TOPIC_ID",
        "ERROR_LOG_TOPIC_ID",
        "INDEX_CHANNEL_ID",
        "FILE_SHARING_CHANNEL_ID",
    ]
    missing = [var for var in required_vars if not getattr(settings, var, None)]

    if missing:
        await send_missing_var_log(bot, missing, context_action="Bot Startup Configuration Check")

    # Verify bot is admin in INDEX_CHANNEL_ID and FILE_SHARING_CHANNEL_ID
    try:
        me = await bot.get_me()
        for label, var_name in [
            ("Indexed File Database Channel", "INDEX_CHANNEL_ID"),
            ("File Sharing Channel", "FILE_SHARING_CHANNEL_ID"),
        ]:
            cid = getattr(settings, var_name, None)
            if cid:
                try:
                    member = await bot.get_chat_member(int(cid), me.id)
                    if getattr(member, "status", "") not in ("administrator", "creator"):
                        await send_bot_not_admin_log(
                            bot=bot,
                            chat_title=label,
                            chat_id=cid,
                            missing_permission="Administrator",
                            action=f"Startup Check ({var_name})",
                        )
                except Exception as e:
                    await send_bot_not_admin_log(
                        bot=bot,
                        chat_title=label,
                        chat_id=cid,
                        missing_permission=f"Bot not in chat or not Admin ({e})",
                        action=f"Startup Check ({var_name})",
                    )
    except Exception:
        pass

    status_msg = (
        "Online & Polling Started (with missing var warnings)"
        if missing
        else "Online & Polling Started (All Required Variables Verified)"
    )
    await send_deployment_log(
        bot=bot,
        event_type="Bot Startup / Render Live",
        status_text=status_msg,
        is_error=bool(missing),
          )
