from telebot import TeleBot, types
import sqlite3
import time
import random

BOT_TOKEN = "8452391283:AAESGiQ0GClTdX8aElJonmj3194lpNin00M"
ADMIN_ID = 7617397626
TRIGGER_KEYWORD = "#konkurs"

bot = TeleBot(BOT_TOKEN, parse_mode='HTML')
conn = sqlite3.connect("universal_konkurs.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS channels (chat_id INTEGER PRIMARY KEY, username TEXT, added_by INTEGER, bot_is_admin INTEGER, added_at INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS contests (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, trigger_message_id INTEGER, contest_message_id INTEGER, kind TEXT, status TEXT, created_by INTEGER, created_at INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS participants (id INTEGER PRIMARY KEY AUTOINCREMENT, contest_id INTEGER, user_id INTEGER, username TEXT, joined_at INTEGER)")
conn.commit()

def main_menu_markup():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🛰 Kanal qo'shish", callback_data="add_channel"))
    kb.add(types.InlineKeyboardButton("📋 Qanday ishlaydi?", callback_data="how"))
    return kb

def contest_type_markup(contest_db_id):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🎤 Ovozli konkurs", callback_data=f"type_voice|{contest_db_id}"),
        types.InlineKeyboardButton("🔗 Taklif havolali konkurs", callback_data=f"type_referral|{contest_db_id}"),
        types.InlineKeyboardButton("⚔️ Batl konkursi", callback_data=f"type_batl|{contest_db_id}"),
        types.InlineKeyboardButton("🎲 Random konkurs", callback_data=f"type_random|{contest_db_id}")
    )
    return kb

def join_markup(contest_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Qatnashish", callback_data=f"join|{contest_id}"))
    return kb

@bot.message_handler(commands=['start'])
def handle_start(m):
    if m.from_user.id == ADMIN_ID:
        bot.send_message(m.chat.id, "👋 Salom, admin! Kanal qo'shing yoki kanalga #konkurs yuborib konkurs boshlang.", reply_markup=main_menu_markup())
    else:
        bot.send_message(m.chat.id, "🤖 Salom! Men Universal Konkurs Botman.\nKonkursni boshlash uchun kanalni botga admin qiling va kanalga #konkurs so'zini yuboring. Kanal qo'shish uchun tugmani bosing.", reply_markup=main_menu_markup())

@bot.callback_query_handler(func=lambda c: c.data == "how")
def how_cb(c):
    bot.answer_callback_query(c.id)
    text = "Ish tartibi:\n1) Admin botni kanalga admin qiladi.\n2) Admin kanalga #konkurs yozadi.\n3) Bot konkursni tanlab e'lon qiladi.\n4) Foydalanuvchilar qatnashadi. Kanalga !stop yozilsa konkurs tugaydi."
    bot.send_message(c.message.chat.id, text)

@bot.callback_query_handler(func=lambda c: c.data == "add_channel")
def add_channel_cb(c):
    bot.answer_callback_query(c.id)
    if c.from_user.id != ADMIN_ID:
        bot.send_message(c.message.chat.id, "Faqat admin kanal qo'sha oladi.")
        return
    bot.send_message(c.message.chat.id, "Kanalni qo'shish uchun kanalning istalgan postini shu chatga *forward* qiling yoki kanal username (@username) yuboring.")

@bot.message_handler(func=lambda m: m.forward_from_chat is not None or (m.text and m.text.startswith("@")))
def register_channel(m):
    if m.from_user.id != ADMIN_ID:
        return
    chat = None
    if m.forward_from_chat:
        chat = m.forward_from_chat
    else:
        try:
            username = m.text.split()[0]
            chat = bot.get_chat(username)
        except Exception:
            bot.reply_to(m, "Kanal topilmadi. Iltimos kanal username ni to'g'ri yuboring yoki kanaldan postni forward qiling.")
            return
    try:
        bot_member = bot.get_me()
        check = bot.get_chat_member(chat.id, bot_member.id)
        is_admin = 1 if check.status in ["administrator", "creator"] else 0
    except Exception:
        is_admin = 0
    cur.execute("INSERT OR REPLACE INTO channels (chat_id, username, added_by, bot_is_admin, added_at) VALUES (?, ?, ?, ?, ?)",
                (chat.id, getattr(chat, "username", None) or "", m.from_user.id, is_admin, int(time.time())))
    conn.commit()
    if is_admin:
        bot.reply_to(m, f"Kanal muvaffaqiyatli qo'shildi: {getattr(chat,'title', chat.id)}. Bot kanalda admin ekan.")
    else:
        bot.reply_to(m, "Kanal qo'shildi, lekin bot kanalda admin emas. Iltimos botni kanalga admin qiling va yana forward qiling.")

@bot.channel_post_handler(func=lambda m: True)
def handle_channel_post(post):
    text = (post.text or post.caption or "").lower()
    if TRIGGER_KEYWORD in text:
        cur.execute("SELECT bot_is_admin FROM channels WHERE chat_id=?", (post.chat.id,))
        row = cur.fetchone()
        if not row:
            return
        if row[0] != 1:
            bot.send_message(post.chat.id, "Bot kanalda admin emas. Iltimos botni admin qiling.")
            return
        now = int(time.time())
        cur.execute("INSERT INTO contests (chat_id, trigger_message_id, contest_message_id, kind, status, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (post.chat.id, post.message_id, 0, "awaiting", "awaiting", 0, now))
        conn.commit()
        cur.execute("SELECT id FROM contests WHERE chat_id=? AND trigger_message_id=? ORDER BY created_at DESC LIMIT 1", (post.chat.id, post.message_id))
        contest_id = cur.fetchone()[0]
        bot.send_message(post.chat.id, "🎉 Qaysi turdagi konkursni boshlaymiz?", reply_to_message_id=post.message_id, reply_markup=contest_type_markup(contest_id))

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("type_"))
def type_select(c):
    bot.answer_callback_query(c.id)
    parts = c.data.split("|")
    payload = parts[0]
    contest_db_id = int(parts[1]) if len(parts) > 1 else None
    if not contest_db_id:
        bot.send_message(c.message.chat.id, "Konkurs topilmadi.")
        return
    kind = payload.replace("type_", "")
    cur.execute("SELECT status, chat_id, trigger_message_id FROM contests WHERE id=?", (contest_db_id,))
    row = cur.fetchone()
    if not row:
        bot.send_message(c.message.chat.id, "Konkurs topilmadi.")
        return
    status, chat_id, trigger_msg_id = row
    if status != "awaiting":
        bot.send_message(c.message.chat.id, "Bu konkurs allaqachon sozlangan yoki aktiv.")
        return
    post_text = ""
    if kind == "voice":
        post_text = "<b>🎤 Ovozli konkurs</b>\nIshtirok etish uchun pastdagi tugmani bosing. Har bir foydalanuvchi bir marta qo'shiladi."
    elif kind == "referral":
        post_text = "<b>🔗 Taklif havolali konkurs</b>\nSizga shaxsiy taklif havolasi beriladi."
    elif kind == "batl":
        post_text = "<b>⚔️ Batl konkursi</b>\nIshtirokchilar post yuboradi va reaksiyalar ball beradi."
    else:
        post_text = "<b>🎲 Random konkurs</b>\nMaxsus shartlar asosida g'oliblar tasodifiy tanlanadi."
    sent = bot.send_message(chat_id, post_text, parse_mode='HTML', reply_to_message_id=trigger_msg_id)
    join_msg = bot.send_message(chat_id, "Ishtirok etish uchun:", reply_to_message_id=sent.message_id, reply_markup=join_markup(contest_db_id))
    cur.execute("UPDATE contests SET contest_message_id=?, kind=?, status='active', created_by=?, created_at=? WHERE id=?",
                (sent.message_id, kind, c.from_user.id, int(time.time()), contest_db_id))
    conn.commit()
    bot.send_message(c.message.chat.id, "✅ Konkurs e'lon qilindi.")

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("join|"))
def join_cb(c):
    bot.answer_callback_query(c.id)
    try:
        contest_id = int(c.data.split("|",1)[1])
    except:
        bot.send_message(c.message.chat.id, "Noto'g'ri so'rov.")
        return
    cur.execute("SELECT kind, status, chat_id FROM contests WHERE id=?", (contest_id,))
    row = cur.fetchone()
    if not row:
        bot.send_message(c.message.chat.id, "Konkurs topilmadi.")
        return
    kind, status, chat_id = row
    if status != "active":
        bot.send_message(c.message.chat.id, "Konkurs faol emas.")
        return
    user_id = c.from_user.id
    username = c.from_user.username or c.from_user.first_name
    cur.execute("SELECT 1 FROM participants WHERE contest_id=? AND user_id=?", (contest_id, user_id))
    if cur.fetchone():
        bot.send_message(c.message.chat.id, "Siz allaqachon qatnashyapsiz.")
        return
    cur.execute("INSERT INTO participants (contest_id, user_id, username, joined_at) VALUES (?, ?, ?, ?)", (contest_id, user_id, username, int(time.time())))
    conn.commit()
    bot.send_message(chat_id, f"✅ @{username} konkursga qo'shildi!")
    cur.execute("SELECT username FROM participants WHERE contest_id=?", (contest_id,))
    names = cur.fetchall()
    text = f"<b>Ro'yxat ({len(names)}):</b>\n"
    for n in names:
        text += f"• {n[0]}\n"
    try:
        bot.edit_message_text(text, chat_id, c.message.message_id, parse_mode='HTML', reply_markup=join_markup(contest_id))
    except:
        pass

@bot.message_handler(func=lambda m: m.chat.type == "channel" and m.text and m.text.strip().lower() == "!stop")
def stop_in_channel(m):
    chat_id = m.chat.id
    cur.execute("SELECT id, kind FROM contests WHERE chat_id=? AND status='active' ORDER BY created_at DESC LIMIT 1", (chat_id,))
    row = cur.fetchone()
    if not row:
        return
    contest_id, kind = row
    cur.execute("SELECT username FROM participants WHERE contest_id=?", (contest_id,))
    rows = cur.fetchall()
    participants = [r[0] for r in rows]
    if not participants:
        bot.send_message(chat_id, "Konkurs tugadi. Ishtirokchilar topilmadi.")
    else:
        result = "<b>Konkurs yakunlandi!</b>\n\nG'oliblar:\n"
        if kind == "random":
            winner = random.choice(participants)
            result += f"🎉 {winner}\n"
        else:
            counts = {}
            for p in participants:
                counts[p] = counts.get(p, 0) + 1
            sorted_p = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            for i, (nick, cnt) in enumerate(sorted_p[:5], start=1):
                result += f"{i}. {nick} — {cnt} bal\n"
        bot.send_message(chat_id, result, parse_mode='HTML')
    cur.execute("UPDATE contests SET status='finished' WHERE id=?", (contest_id,))
    conn.commit()

if __name__ == "__main__":
    bot.polling(none_stop=True)
