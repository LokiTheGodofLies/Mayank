"""
config/strings.py
Stores default templates and metadata for all 16 customizable bot scripts.
"""

SCRIPT_METADATA = {
    "start": {
        "index": 1,
        "title": "1. Start Script",
        "description": "Welcome message sent when a user runs /start.",
        "placeholders": ["{user_name}", "{username}", "{user_id}", "{user_link}", "{user_role}", "{bot_name}", "{bot_username}", "{bot_link}"],
    },
    "search_usage": {
        "index": 2,
        "title": "2. Search Usage Script",
        "description": "Prompt shown when a user sends /search without a keyword.",
        "placeholders": ["{user_name}", "{user_link}"],
    },
    "search_results": {
        "index": 3,
        "title": "3. Search Results Script",
        "description": "Header message shown above paginated book search results.",
        "placeholders": ["{query}", "{file_type}", "{total}", "{page}", "{total_pages}"],
    },
    "search_no_results": {
        "index": 4,
        "title": "4. Search No Results Script",
        "description": "Message shown when no book/audiobook matches the keyword.",
        "placeholders": ["{query}", "{file_type}"],
    },
    "file_delivery": {
        "index": 5,
        "title": "5. File Delivery Script",
        "description": "Notice sent when a file is forwarded to the File Sharing Channel.",
        "placeholders": ["{file_name}", "{file_size}", "{duration}", "{delete_minutes}"],
    },
    "auto_deleted": {
        "index": 6,
        "title": "6. Auto Deleted Script",
        "description": "Optional notice shown after the file timer expires and deletes the file.",
        "placeholders": ["{file_name}", "{delete_minutes}"],
    },
    "index_usage": {
        "index": 7,
        "title": "7. Index Usage Script",
        "description": "Instructions shown when /index is sent without parameters.",
        "placeholders": ["{user_name}", "{user_link}"],
    },
    "forward_status": {
        "index": 8,
        "title": "8. Forward Status Script",
        "description": "Live progress box updated during batch /index.",
        "placeholders": ["{fetched}", "{remaining}", "{forwarded}", "{duplicate}", "{deleted}", "{skipped}", "{filtered}", "{status}", "{percentage}", "{footer}"],
    },
    "index_completed": {
        "index": 9,
        "title": "9. Index Completed Script",
        "description": "Summary message shown when batch indexing finishes.",
        "placeholders": ["{chat_title}", "{chat_id}", "{fetched}", "{forwarded}", "{duplicate}", "{deleted}", "{skipped}", "{filtered}", "{date_time}"],
    },
    "access_denied": {
        "index": 10,
        "title": "10. Access Denied Script",
        "description": "Message shown when a normal user tries to run an Admin/Owner command.",
        "placeholders": ["{user_name}", "{user_link}", "{user_id}"],
    },
    "user_log": {
        "index": 11,
        "title": "11. User Log Script",
        "description": "Log message sent to User Logs Topic (5) when a user starts the bot.",
        "placeholders": ["{bot_link}", "{user_name}", "{username}", "{user_id}", "{user_link}", "{user_role}", "{date_time}"],
    },
    "group_log": {
        "index": 12,
        "title": "12. Group Log Script",
        "description": "Log message sent to Group Logs Topic (18) when added, removed, or permissions change.",
        "placeholders": ["{status}", "{bot_link}", "{chat_title}", "{action}", "{chat_id}", "{chat_username}", "{invite_link}", "{user_role}", "{permissions}", "{user_name}", "{username}", "{user_id}", "{user_link}", "{date_time}"],
    },
    "channel_log": {
        "index": 13,
        "title": "13. Channel Log Script",
        "description": "Log message sent to Channel Logs Topic (19) when added, removed, or permissions change.",
        "placeholders": ["{status}", "{bot_link}", "{chat_title}", "{action}", "{chat_id}", "{chat_username}", "{invite_link}", "{user_role}", "{permissions}", "{user_name}", "{username}", "{user_id}", "{user_link}", "{date_time}"],
    },
    "file_index_log": {
        "index": 14,
        "title": "14. File Index Log Script",
        "description": "Log message sent to Index Logs Topic (32) when a new file is indexed.",
        "placeholders": ["{status}", "{file_name}", "{file_type}", "{extension}", "{file_size}", "{duration}", "{file_id}", "{caption}", "{chat_title}", "{chat_id}", "{invite_link}", "{user_name}", "{username}", "{user_id}", "{user_link}", "{date_time}"],
    },
    "vars_list": {
        "index": 15,
        "title": "15. Vars List Script",
        "description": "Header template for /getvars variable listing.",
        "placeholders": ["{status}", "{user_link}", "{date_time}"],
    },
    "error_log": {
        "index": 16,
        "title": "16. Error Log Script",
        "description": "Error alert template sent to Error Logs Topic (35) when an exception occurs.",
        "placeholders": ["{action}", "{chat_title}", "{chat_id}", "{user_link}", "{user_id}", "{status}", "{date_time}"],
    },
}

DEFAULT_SCRIPTS = {
    "start": "hi I am just a telegram bot under test",
    "search_usage": (
        "⚠️ <b>Please provide a search keyword!</b>\n"
        "<b>Example:</b> <code>/search Atomic Habits</code>"
    ),
    "search_results": (
        "🔍 <b>Search Results for:</b> <code>{query}</code>\n"
        "<b>• Filter:</b> {file_type}\n"
        "<b>• Total Found:</b> <code>{total}</code>\n"
        "<b>• Page:</b> <code>{page}/{total_pages}</code>\n\n"
        "<i>Select a file below to send it to the File Sharing Channel:</i>"
    ),
    "search_no_results": (
        "❌ <b>No files found matching:</b> <code>{query}</code>\n"
        "<b>• Filter:</b> {file_type}"
    ),
    "file_delivery": (
        "this file will be deleted after {delete_minutes} min please forward it "
        "to saved message or any other chat"
    ),
    "auto_deleted": (
        "🗑️ <b>File Deleted:</b> <code>{file_name}</code> was automatically removed "
        "after {delete_minutes} minutes."
    ),
    "index_usage": (
        "📥 <b>Batch File Indexer Usage:</b>\n\n"
        "<code>/index &lt;chat_id_or_link&gt; &lt;last_msg_id&gt; [skip_msg_id] [topic_id]</code>\n\n"
        "<b>Example:</b> <code>/index -1001234567890 2500 0</code>"
    ),
    "forward_status": (
        "<pre>╔════❰ ғᴏʀᴡᴀʀᴅ sᴛᴀᴛᴜs  ❱═❍⊱❁۪۪\n"
        "║╭━━━━━━━━━━━━━━━➣\n"
        "║┣⪼𖨠 ғᴇᴄʜᴇᴅ ᴍᴇssᴀɢᴇs: {fetched}\n"
        "║┃\n"
        "║┣⪼𖨠 ʀᴇᴍᴀɪɴɪɴɢ ᴍᴇssᴀɢᴇs: {remaining}\n"
        "║┃\n"
        "║┣⪼𖨠 sᴜᴄᴄᴇғᴜʟʟʏ ғᴏʀᴡᴀʀᴅᴇᴅ: {forwarded}\n"
        "║┃\n"
        "║┣⪼𖨠 ᴅᴜᴘʟɪᴄᴀᴛᴇ ᴍᴇssᴀɢᴇs: {duplicate}\n"
        "║┃\n"
        "║┣⪼𖨠 ᴅᴇʟᴇᴛᴇᴅ ᴍᴇssᴀɢᴇs: {deleted}\n"
        "║┃\n"
        "║┣⪼𖨠 sᴋɪᴘᴘᴇᴅ ᴍᴇssᴀɢᴇs: {skipped}\n"
        "║┃\n"
        "║┣⪼𖨠 ғɪʟᴛᴇʀᴇᴅ ᴍᴇssᴀɢᴇs: {filtered}\n"
        "║┃\n"
        "║┣⪼𖨠 ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs: {status}\n"
        "║┃\n"
        "║┣⪼𖨠 ᴘᴇʀᴄᴇɴᴛᴀɢᴇ: {percentage} %\n"
        "║╰━━━━━━━━━━━━━━━➣\n"
        "╚═════❰ {footer} ❱══❍⊱❁۪۪</pre>"
    ),
    "index_completed": (
        "✅ <b>Batch Indexing Completed!</b>\n\n"
        "<b>• Source Chat:</b> {chat_title} (<code>{chat_id}</code>)\n"
        "<b>• Fetched Messages:</b> <code>{fetched}</code>\n"
        "<b>• Successfully Forwarded:</b> <code>{forwarded}</code>\n"
        "<b>• Duplicate Messages:</b> <code>{duplicate}</code>\n"
        "<b>• Deleted Messages:</b> <code>{deleted}</code>\n"
        "<b>• Skipped Messages:</b> <code>{skipped}</code>\n"
        "<b>• Filtered Messages:</b> <code>{filtered}</code>\n"
        "<b>• Date &amp; Time:</b> <code>{date_time}</code>"
    ),
    "access_denied": (
        "🚫 <b>Access Denied!</b>\n"
        "Only Bot Owners and Admins can use this command."
    ),
    "user_log": (
        "<b>#New_User_Start</b>\n"
        "A new user started {bot_link}\n"
        "<b>User Name:</b> {user_name}\n"
        "<b>Username:</b> {username}\n"
        "<b>Telegram ID:</b> <code>{user_id}</code>\n"
        "<b>Profile Link:</b> {user_link}\n"
        "<b>User Role:</b> <code>{user_role}</code>\n"
        "<b>Date &amp; Time:</b> <code>{date_time}</code>"
    ),
    "group_log": (
        "<b>#{status}</b>\n"
        "{bot_link} status updated in Group: <b>{chat_title}</b>\n"
        "<b>Action:</b> {action}\n"
        "<b>Group ID:</b> <code>{chat_id}</code> | <b>Username:</b> {chat_username}\n"
        "<b>Group Link:</b> {invite_link}\n"
        "<b>Bot Role:</b> <code>{user_role}</code>\n"
        "<b>Allowed Permissions:</b>\n"
        "{permissions}\n"
        "<b>Action By User:</b>\n"
        "• <b>Name:</b> {user_name} | <b>Username:</b> {username}\n"
        "• <b>User ID:</b> <code>{user_id}</code> | <b>Profile Link:</b> {user_link}\n"
        "<b>Date &amp; Time:</b> <code>{date_time}</code>"
    ),
    "channel_log": (
        "<b>#{status}</b>\n"
        "{bot_link} status updated in Channel: <b>{chat_title}</b>\n"
        "<b>Action:</b> {action}\n"
        "<b>Channel ID:</b> <code>{chat_id}</code> | <b>Username:</b> {chat_username}\n"
        "<b>Channel Link:</b> {invite_link}\n"
        "<b>Bot Role:</b> <code>{user_role}</code>\n"
        "<b>Allowed Permissions:</b>\n"
        "{permissions}\n"
        "<b>Action By User:</b>\n"
        "• <b>Name:</b> {user_name} | <b>Username:</b> {username}\n"
        "• <b>User ID:</b> <code>{user_id}</code> | <b>Profile Link:</b> {user_link}\n"
        "<b>Date &amp; Time:</b> <code>{date_time}</code>"
    ),
    "file_index_log": (
        "<b>#{status}</b>\n\n"
        "<b>• File Name:</b> <code>{file_name}</code>\n"
        "<b>• File Type:</b> {file_type}\n"
        "<b>• Extension:</b> <code>.{extension}</code>\n"
        "<b>• File Size:</b> <code>{file_size}</code>\n"
        "<b>• Duration:</b> <code>{duration}</code>\n"
        "<b>• File ID:</b> <code>{file_id}</code>\n"
        "<b>• Caption:</b> {caption}\n\n"
        "<b>• Source Chat:</b> {chat_title}\n"
        "<b>• Source Chat ID:</b> <code>{chat_id}</code>\n"
        "<b>• Indexed DB Link:</b> {invite_link}\n"
        "<b>• Date &amp; Time:</b> <code>{date_time}</code>"
    ),
    "vars_list": (
        "⚙️ <b>Configured Environment Variables</b>\n\n"
        "{status}\n\n"
        "<b>• Checked By:</b> {user_link}\n"
        "<b>• Date &amp; Time:</b> <code>{date_time}</code>"
    ),
    "error_log": (
        "🚨 <b>#BOT_ERROR_LOG</b>\n\n"
        "<b>• Action:</b> <code>{action}</code>\n"
        "<b>• Chat:</b> {chat_title} (<code>{chat_id}</code>)\n"
        "<b>• User:</b> {user_link} (<code>{user_id}</code>)\n"
        "<b>• Error Details:</b>\n<pre>{status}</pre>\n"
        "<b>• Date &amp; Time:</b> <code>{date_time}</code>"
    ),
}

# Support uppercase aliases (e.g. START_SCRIPT -> start)
for _key, _val in list(DEFAULT_SCRIPTS.items()):
    DEFAULT_SCRIPTS[f"{_key.upper()}_SCRIPT"] = _val

SCRIPT_KEYS_ORDER = list(SCRIPT_METADATA.keys())
SCRIPT_TITLES = {k: v["title"] for k, v in SCRIPT_METADATA.items()}

PLACEHOLDERS_HELP_TEXT = (
    "<b>📌 Supported Placeholders You Can Use:</b>\n\n"
    "<b>👤 User:</b>\n"
    "<code>{user_name}</code>, <code>{username}</code>, <code>{user_id}</code>, "
    "<code>{user_link}</code>, <code>{user_role}</code>\n\n"
    "<b>🤖 Bot:</b>\n"
    "<code>{bot_name}</code>, <code>{bot_username}</code>, <code>{bot_link}</code>\n\n"
    "<b>📚 File:</b>\n"
    "<code>{file_name}</code>, <code>{file_size}</code>, <code>{file_id}</code>, "
    "<code>{duration}</code>, <code>{caption}</code>, <code>{extension}</code>, "
    "<code>{file_type}</code>, <code>{delete_minutes}</code>\n\n"
    "<b>💬 Chat &amp; Logs:</b>\n"
    "<code>{chat_title}</code>, <code>{chat_id}</code>, <code>{chat_username}</code>, "
    "<code>{invite_link}</code>, <code>{topic_id}</code>, <code>{permissions}</code>, "
    "<code>{action}</code>, <code>{date_time}</code>\n\n"
    "<b>🔍 Search &amp; Indexer:</b>\n"
    "<code>{query}</code>, <code>{total}</code>, <code>{page}</code>, <code>{total_pages}</code>, "
    "<code>{fetched}</code>, <code>{remaining}</code>, <code>{forwarded}</code>, "
    "<code>{duplicate}</code>, <code>{deleted}</code>, <code>{skipped}</code>, "
    "<code>{filtered}</code>, <code>{status}</code>, <code>{percentage}</code>, <code>{footer}</code>"
)
