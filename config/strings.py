"""
config/strings.py
Stores all default text messages, log formats, and placeholder definitions for the 16 bot scripts.
"""

# Ordered list of all 16 scripts (Page 1: 1–10, Page 2: 11–16 in /editscript)
SCRIPT_KEYS_ORDER = [
    # Page 1 (1–10)
    "START_SCRIPT",
    "SEARCH_USAGE_SCRIPT",
    "SEARCH_RESULTS_SCRIPT",
    "SEARCH_NO_RESULTS_SCRIPT",
    "FILE_DELIVERY_SCRIPT",
    "AUTO_DELETED_SCRIPT",
    "INDEX_USAGE_SCRIPT",
    "FORWARD_STATUS_SCRIPT",
    "INDEX_COMPLETED_SCRIPT",
    "ACCESS_DENIED_SCRIPT",
    # Page 2 (11–16)
    "USER_LOG_SCRIPT",
    "GROUP_LOG_SCRIPT",
    "CHANNEL_LOG_SCRIPT",
    "FILE_INDEX_LOG_SCRIPT",
    "VARS_LIST_SCRIPT",
    "ERROR_LOG_SCRIPT",
]

# Button titles displayed in the /editscript menu
SCRIPT_TITLES = {
    "START_SCRIPT": "1. Start Script",
    "SEARCH_USAGE_SCRIPT": "2. Search Usage Script",
    "SEARCH_RESULTS_SCRIPT": "3. Search Results Script",
    "SEARCH_NO_RESULTS_SCRIPT": "4. Search No Results Script",
    "FILE_DELIVERY_SCRIPT": "5. File Delivery Script",
    "AUTO_DELETED_SCRIPT": "6. Auto Deleted Script",
    "INDEX_USAGE_SCRIPT": "7. Index Usage Script",
    "FORWARD_STATUS_SCRIPT": "8. Forward Status Script",
    "INDEX_COMPLETED_SCRIPT": "9. Index Completed Script",
    "ACCESS_DENIED_SCRIPT": "10. Access Denied Script",
    "USER_LOG_SCRIPT": "11. User Log Script",
    "GROUP_LOG_SCRIPT": "12. Group Log Script",
    "CHANNEL_LOG_SCRIPT": "13. Channel Log Script",
    "FILE_INDEX_LOG_SCRIPT": "14. File Index Log Script",
    "VARS_LIST_SCRIPT": "15. Vars List Script",
    "ERROR_LOG_SCRIPT": "16. Error Log Script",
}

# Default templates for all 16 scripts
DEFAULT_SCRIPTS = {
    "START_SCRIPT": "hi I am just a telegram bot under test",
    "SEARCH_USAGE_SCRIPT": (
        "⚠️ <b>Please provide a search keyword!</b>\n"
        "<b>Example:</b> <code>/search Atomic Habits</code>"
    ),
    "SEARCH_RESULTS_SCRIPT": (
        "🔍 <b>Search Results for:</b> <code>{query}</code>\n"
        "<b>• Filter:</b> {file_type}\n"
        "<b>• Total Found:</b> <code>{total}</code>\n"
        "<b>• Page:</b> <code>{page}/{total_pages}</code>\n\n"
        "<i>Select a file below to send it to the File Sharing Channel:</i>"
    ),
    "SEARCH_NO_RESULTS_SCRIPT": (
        "❌ <b>No files found matching:</b> <code>{query}</code>\n"
        "<b>• Filter:</b> {file_type}"
    ),
    "FILE_DELIVERY_SCRIPT": (
        "this file will be deleted after {delete_minutes} min please forward it "
        "to saved message or any other chat"
    ),
    "AUTO_DELETED_SCRIPT": (
        "🗑️ <b>File Deleted:</b> <code>{file_name}</code> was removed after {delete_minutes} minutes."
    ),
    "INDEX_USAGE_SCRIPT": (
        "📥 <b>Batch File Indexer Usage:</b>\n\n"
        "<code>/index &lt;chat_id_or_link&gt; &lt;last_msg_id&gt; [skip_msg_id] [topic_id]</code>\n\n"
        "<b>Example:</b> <code>/index -1001234567890 2500 0</code>\n"
        "<i>Or forward the last message from the source channel/group directly after /index.</i>"
    ),
    "FORWARD_STATUS_SCRIPT": (
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
    "INDEX_COMPLETED_SCRIPT": (
        "✅ <b>Batch Indexing Completed!</b>\n\n"
        "<b>• Source Chat:</b> {chat_title} (<code>{chat_id}</code>)\n"
        "<b>• Fetched Messages:</b> <code>{fetched}</code>\n"
        "<b>• Successfully Forwarded / Synced:</b> <code>{forwarded}</code>\n"
        "<b>• Duplicate Messages:</b> <code>{duplicate}</code>\n"
        "<b>• Deleted Messages:</b> <code>{deleted}</code>\n"
        "<b>• Skipped Messages:</b> <code>{skipped}</code>\n"
        "<b>• Filtered Messages:</b> <code>{filtered}</code>\n"
        "<b>• Date &amp; Time:</b> <code>{date_time}</code>"
    ),
    "ACCESS_DENIED_SCRIPT": (
        "🚫 <b>Access Denied!</b>\n"
        "Only Bot Owners and Admins can use this command."
    ),
    "USER_LOG_SCRIPT": (
        "<b>#New_User_Start</b>\n"
        "A new user started {bot_link}\n"
        "<b>User Name:</b> {user_name}\n"
        "<b>Username:</b> {username}\n"
        "<b>Telegram ID:</b> <code>{user_id}</code>\n"
        "<b>Profile Link:</b> {user_link}\n"
        "<b>User Role:</b> <code>{user_role}</code>\n"
        "<b>Date &amp; Time:</b> <code>{date_time}</code>"
    ),
    "GROUP_LOG_SCRIPT": (
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
    "CHANNEL_LOG_SCRIPT": (
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
    "FILE_INDEX_LOG_SCRIPT": (
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
    "VARS_LIST_SCRIPT": (
        "⚙️ <b>Configured Environment Variables</b>\n\n"
        "{status}\n\n"
        "<b>• Checked By:</b> {user_link}\n"
        "<b>• Date &amp; Time:</b> <code>{date_time}</code>"
    ),
    "ERROR_LOG_SCRIPT": (
        "🚨 <b>#BOT_ERROR_LOG</b>\n\n"
        "<b>• Action:</b> <code>{action}</code>\n"
        "<b>• Chat:</b> {chat_title} (<code>{chat_id}</code>)\n"
        "<b>• User:</b> {user_link} (<code>{user_id}</code>)\n"
        "<b>• Error Details:</b>\n<pre>{status}</pre>\n"
        "<b>• Date &amp; Time:</b> <code>{date_time}</code>"
    ),
}

# Placeholder guide shown when an Owner/Admin clicks "✏️ Change Text" in /editscript
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
