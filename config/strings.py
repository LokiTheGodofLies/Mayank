# Default Script Templates and Available Placeholders for /editscript

DEFAULT_SCRIPTS: dict[str, str] = {
    "start": "hi I am just a telegram bot under test",
    "user_log": (
        "<b>#New_User_Start</b>\n\n"
        "A new user started {bot_link}\n\n"
        "<b>User Name:</b> {user_name}\n"
        "<b>Username:</b> {username}\n"
        "<b>Telegram ID:</b> <code>{user_id}</code>\n"
        "<b>Profile Link:</b> {user_link}\n"
        "<b>User Role:</b> <code>{user_role}</code>\n"
        "<b>Date & Time:</b> <code>{date_time}</code>"
    ),
    "group_log": (
        "<b>#Group_{action_tag}</b>\n\n"
        "{bot_link} status update in Group: <b>{chat_title}</b>\n"
        "<b>Event:</b> <code>{action_description}</code>\n\n"
        "<b>Group Name:</b> {chat_title}\n"
        "<b>Group ID:</b> <code>{chat_id}</code>\n"
        "<b>Group Username:</b> {chat_username}\n"
        "<b>Group Link:</b> {invite_link}\n"
        "<b>Bot Permissions:</b>\n{permissions}\n\n"
        "<b>Action By User:</b>\n"
        "• <b>Name:</b> {user_name}\n"
        "• <b>Username:</b> {username}\n"
        "• <b>User ID:</b> <code>{user_id}</code>\n"
        "• <b>Profile Link:</b> {user_link}\n\n"
        "<b>Date & Time:</b> <code>{date_time}</code>"
    ),
    "channel_log": (
        "<b>#Channel_{action_tag}</b>\n\n"
        "{bot_link} status update in Channel: <b>{chat_title}</b>\n"
        "<b>Event:</b> <code>{action_description}</code>\n\n"
        "<b>Channel Name:</b> {chat_title}\n"
        "<b>Channel ID:</b> <code>{chat_id}</code>\n"
        "<b>Channel Username:</b> {chat_username}\n"
        "<b>Channel Link:</b> {invite_link}\n"
        "<b>Bot Permissions:</b>\n{permissions}\n\n"
        "<b>Action By User:</b>\n"
        "• <b>Name:</b> {user_name}\n"
        "• <b>Username:</b> {username}\n"
        "• <b>User ID:</b> <code>{user_id}</code>\n"
        "• <b>Profile Link:</b> {user_link}\n\n"
        "<b>Date & Time:</b> <code>{date_time}</code>"
    ),
    "file_index_log": (
        "<b>📥 #File_Indexed</b>\n\n"
        "<b>File Name:</b> <code>{file_name}</code>\n"
        "<b>Category:</b> <code>{file_type}</code> (<code>.{extension}</code>)\n"
        "<b>File Size:</b> <code>{file_size}</code>\n"
        "<b>Duration:</b> <code>{duration}</code>\n"
        "<b>Caption:</b> {caption}\n"
        "<b>Source Chat:</b> {chat_title} (<code>{chat_id}</code>)\n"
        "<b>Topic ID:</b> <code>{topic_id}</code>\n"
        "<b>DB Message ID:</b> <code>{db_message_id}</code>\n"
        "<b>Date & Time:</b> <code>{date_time}</code>"
    ),
    "index_usage": (
        "<b>📥 Batch File Indexer & Forwarder</b>\n\n"
        "<b>Usage:</b>\n"
        "<code>/index &lt;chat_link_or_id&gt; [last_msg_id] [skip_msg_id] [topic_id]</code>\n\n"
        "<b>Examples:</b>\n"
        "• Using message link to last post:\n"
        "  <code>/index https://t.me/c/1234567890/5000</code>\n"
        "• With Skip Number (start after message 1000):\n"
        "  <code>/index https://t.me/c/1234567890/5000 1000</code>\n"
        "• With Skip Number + Forum Topic ID (e.g. topic 15):\n"
        "  <code>/index https://t.me/c/1234567890/5000 1000 15</code>"
    ),
    "forward_status": (
        "╔════❰ ғᴏʀᴡᴀʀᴅ sᴛᴀᴛᴜs  ❱═❍⊱❁۪۪\n"
        "║╭━━━━━━━━━━━━━━━➣\n"
        "║┣⪼𖨠 ғᴇᴄʜᴇᴅ ᴍᴇssᴀɢᴇs: <code>{fetched}</code>\n"
        "║┃\n"
        "║┣⪼𖨠 ʀᴇᴍᴀɪɴɪɴɢ ᴍᴇssᴀɢᴇs: <code>{remaining}</code>\n"
        "║┃\n"
        "║┣⪼𖨠 sᴜᴄᴄᴇғᴜʟʟʏ ғᴏʀᴡᴀʀᴅᴇᴅ: <code>{forwarded}</code>\n"
        "║┃\n"
        "║┣⪼𖨠 ᴅᴜᴘʟɪᴄᴀᴛᴇ ᴍᴇssᴀɢᴇs: <code>{duplicate}</code>\n"
        "║┃\n"
        "║┣⪼𖨠 ᴅᴇʟᴇᴛᴇᴅ ᴍᴇssᴀɢᴇs: <code>{deleted}</code>\n"
        "║┃\n"
        "║┣⪼𖨠 sᴋɪᴘᴘᴇᴅ ᴍᴇssᴀɢᴇs: <code>{skipped}</code>\n"
        "║┃\n"
        "║┣⪼𖨠 ғɪʟᴛᴇʀᴇᴅ ᴍᴇssᴀɢᴇs: <code>{filtered}</code>\n"
        "║┃\n"
        "║┣⪼𖨠 ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs: <code>{status}</code>\n"
        "║┃\n"
        "║┣⪼𖨠 ᴘᴇʀᴄᴇɴᴛᴀɢᴇ: <code>{percentage} %</code>\n"
        "║╰━━━━━━━━━━━━━━━➣ \n"
        "╚═════❰ {footer} ❱══❍⊱❁۪۪"
    ),
    "index_completed": (
        "✅ <b>Batch Indexing Finished!</b>\n\n"
        "• <b>Fetched Messages:</b> <code>{fetched}</code>\n"
        "• <b>Successfully Indexed/Forwarded:</b> <code>{forwarded}</code>\n"
        "• <b>Duplicates Skipped:</b> <code>{duplicate}</code>\n"
        "• <b>Deleted Messages:</b> <code>{deleted}</code>\n"
        "• <b>Skipped Messages:</b> <code>{skipped}</code>\n"
        "• <b>Filtered (Non-Book/Audio):</b> <code>{filtered}</code>"
    ),
    "search_usage": (
        "🔍 <b>Please enter a book or audiobook keyword to search!</b>\n"
        "<b>Example:</b> <code>/search Atomic Habits</code>"
    ),
    "search_results": (
        "📚 <b>Search Results for:</b> <code>{query}</code>\n"
        "Found <b>{total}</b> file(s) • Page <b>{page}/{total_pages}</b>\n"
        "<i>Tap a file button below to get it:</i>"
    ),
    "search_no_results": (
        "❌ <b>No matching eBooks or Audiobooks found for:</b> <code>{query}</code>\n"
        "<i>Check your spelling or try searching with fewer words.</i>"
    ),
    "file_delivery": (
        "📚 <b>File Name:</b> <code>{file_name}</code>\n"
        "📦 <b>File Size:</b> <code>{file_size}</code>\n"
        "🏷 <b>Format:</b> <code>.{extension}</code> ({file_type})\n"
        "⏱ <b>Duration:</b> <code>{duration}</code>\n"
        "📝 <b>Caption:</b> {caption}\n\n"
        "⏳ <i>Note: This file will be automatically deleted in {delete_minutes} minutes. Please forward it to your Saved Messages!</i>"
    ),
    "access_denied": (
        "⛔ <b>Access Denied:</b> You do not have permission to use this command."
    ),
    "vars_list": (
        "⚙️ <b>Current Bot Environment Variables:</b>\n\n{vars_body}"
    ),
    "error_log": (
        "<b>⚠️ #Bot_Error_Log</b>\n\n"
        "<b>Location:</b> <code>{location}</code>\n"
        "<b>Error:</b> <code>{error}</code>\n"
        "<b>Date & Time:</b> <code>{date_time}</code>"
    ),
}

# Human-readable labels and supported placeholders displayed inside /editscript
SCRIPT_METADATA: dict[str, dict[str, str]] = {
    "start": {
        "title": "1. Start Welcome Message (/start)",
        "placeholders": "{user_name}, {username}, {user_id}, {user_link}, {user_role}, {bot_name}, {bot_username}, {bot_link}, {date_time}",
    },
    "user_log": {
        "title": "2. User Start Log (Topic 5)",
        "placeholders": "{user_name}, {username}, {user_id}, {user_link}, {user_role}, {bot_name}, {bot_username}, {bot_link}, {date_time}",
    },
    "group_log": {
        "title": "3. Group Status & Permissions Log (Topic 18)",
        "placeholders": "{action_tag}, {action_description}, {chat_title}, {chat_id}, {chat_username}, {invite_link}, {permissions}, {user_name}, {username}, {user_id}, {user_link}, {bot_name}, {bot_link}, {date_time}",
    },
    "channel_log": {
        "title": "4. Channel Status & Permissions Log (Topic 19)",
        "placeholders": "{action_tag}, {action_description}, {chat_title}, {chat_id}, {chat_username}, {invite_link}, {permissions}, {user_name}, {username}, {user_id}, {user_link}, {bot_name}, {bot_link}, {date_time}",
    },
    "file_index_log": {
        "title": "5. Single File Indexed Log",
        "placeholders": "{file_name}, {file_size}, {file_id}, {extension}, {file_type}, {duration}, {caption}, {chat_title}, {chat_id}, {topic_id}, {db_message_id}, {date_time}",
    },
    "index_usage": {
        "title": "6. Batch /index Usage Help",
        "placeholders": "{user_name}, {bot_name}, {date_time}",
    },
    "forward_status": {
        "title": "7. Batch /index Live Progress Box",
        "placeholders": "{fetched}, {remaining}, {forwarded}, {duplicate}, {deleted}, {skipped}, {filtered}, {status}, {percentage}, {footer}",
    },
    "index_completed": {
        "title": "8. Batch /index Completed Summary",
        "placeholders": "{fetched}, {remaining}, {forwarded}, {duplicate}, {deleted}, {skipped}, {filtered}, {date_time}",
    },
    "search_usage": {
        "title": "9. Search Usage Prompt (/search)",
        "placeholders": "{user_name}, {bot_name}, {date_time}",
    },
    "search_results": {
        "title": "10. Search Results Header",
        "placeholders": "{query}, {total}, {page}, {total_pages}, {user_name}",
    },
    "search_no_results": {
        "title": "11. Search No Results Found",
        "placeholders": "{query}, {user_name}",
    },
    "file_delivery": {
        "title": "12. File Delivery Caption & Auto-Delete Notice",
        "placeholders": "{file_name}, {file_size}, {file_id}, {extension}, {file_type}, {duration}, {caption}, {delete_minutes}, {user_name}, {bot_name}",
    },
    "access_denied": {
        "title": "13. Access Denied Message",
        "placeholders": "{user_name}, {user_id}, {user_role}",
    },
    "vars_list": {
        "title": "14. Environment Variables List (/getvars)",
        "placeholders": "{vars_body}, {date_time}",
    },
    "error_log": {
        "title": "15. Bot Error Log Message",
        "placeholders": "{location}, {error}, {date_time}",
    },
}
