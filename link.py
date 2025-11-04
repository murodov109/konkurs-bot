import sqlite3
from telebot import types

conn = sqlite3.connect("konkurs.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS invites (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    invite_count INTEGER DEFAULT 0
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS joined_users (
    user_id INTEGER PRIMARY KEY,
    inviter_id INTEGER
)
""")
conn.commit()

def link_konkurs(bot, call):
    user_id = call.from_user.id
    username = call.from_user.username or call.from_user.first_name

    cur.execute("INSERT OR IGNORE INTO invites (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

    invite_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔗 Havolani ochish", url=invite_link))
    markup.add(types.InlineKeyboardButton("📊 Reytingni ko‘rish", callback_data="show_invites"))
    
    bot.send_message(
        call.message.chat.id,
        f"🔗 Sizning taklif havolangiz tayyor!\n"
        f"Do‘stlaringizga yuboring:\n\n{invite_link}\n\n"
        f"Har bir yangi foydalanuvchi shu havola orqali kirsa — sizga 1 ball qo‘shiladi 🎉",
        reply_markup=markup
    )

def add_invite(bot, message, inviter_id):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    cur.execute("SELECT * FROM joined_users WHERE user_id=?", (user_id,))
    if cur.fetchone():
        return  # foydalanuvchi allaqachon kirgan

    cur.execute("INSERT INTO joined_users (user_id, inviter_id) VALUES (?, ?)", (user_id, inviter_id))
    cur.execute("UPDATE invites SET invite_count = invite_count + 1 WHERE user_id=?", (inviter_id,))
    cur.execute("INSERT OR IGNORE INTO invites (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

    bot.send_message(inviter_id, f"🎉 Yangi foydalanuvchi sizning havolangiz orqali qo‘shildi: @{username}")

def show_invite_stats(bot, call):
    cur.execute("SELECT username, invite_count FROM invites ORDER BY invite_count DESC LIMIT 10")
    data = cur.fetchall()
    if not data:
        bot.answer_callback_query(call.id, "Hozircha hech kim taklif qilmagan.")
        return

    result = "📊 Eng ko‘p taklif qilganlar:\n\n"
    for i, row in enumerate(data, start=1):
        result += f"{i}. {row[0]} — {row[1]} ta taklif\n"
    bot.send_message(call.message.chat.id, result)
