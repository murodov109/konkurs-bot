import sqlite3
from telebot import types

conn = sqlite3.connect("konkurs.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS voice_participants (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    votes INTEGER DEFAULT 0
)
""")
conn.commit()

def voice_konkurs(bot, call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    join_btn = types.InlineKeyboardButton("🎙 Qatnashish", callback_data="join_voice")
    vote_btn = types.InlineKeyboardButton("🗳 Ovoz berish", callback_data="vote_voice")
    markup.add(join_btn, vote_btn)
    bot.send_message(
        call.message.chat.id,
        "🎤 Ovozniy konkurs boshlandi!\n"
        "Ishtirok etish yoki ovoz berish uchun pastdagi tugmani tanlang.\n"
        "Bot: @unversal_konkurs_bot",
        reply_markup=markup
    )

def add_participant(bot, call):
    user_id = call.from_user.id
    username = call.from_user.username or call.from_user.first_name
    cur.execute("INSERT OR IGNORE INTO voice_participants (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    bot.answer_callback_query(call.id, "✅ Siz ovozniy konkursga qo‘shildingiz!")
    bot.send_message(call.message.chat.id, f"🎙 {username} ishtirokchi sifatida qo‘shildi!")

def vote_for(bot, call):
    user_id = call.from_user.id
    cur.execute("SELECT * FROM voice_participants WHERE user_id=?", (user_id,))
    voter = cur.fetchone()
    if voter:
        bot.answer_callback_query(call.id, "❌ Siz o‘zingizga ovoz bera olmaysiz.")
        return
    cur.execute("SELECT username FROM voice_participants ORDER BY RANDOM() LIMIT 1")
    candidate = cur.fetchone()
    if not candidate:
        bot.answer_callback_query(call.id, "Hozircha ishtirokchilar yo‘q.")
        return
    cur.execute("UPDATE voice_participants SET votes = votes + 1 WHERE username=?", (candidate[0],))
    conn.commit()
    bot.send_message(call.message.chat.id, f"🗳 {call.from_user.username} {candidate[0]} foydalanuvchisiga ovoz berdi!")

def handle_voice_callbacks(bot, call):
    if call.data == "join_voice":
        add_participant(bot, call)
    elif call.data == "vote_voice":
        vote_for(bot, call)
