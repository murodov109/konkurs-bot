from telebot import TeleBot, types
import sqlite3
import json
import random
import time

BOT_TOKEN = "8452391283:AAESGiQ0GClTdX8aElJonmj3194lpNin00M"
ADMIN_ID = 7617397626
BOT_USERNAME = "@unversal_konkurs_bot"
TRIGGER_KEYWORDS = ["#konkurs", "!konkurs", "!startcontest"]

bot = TeleBot(BOT_TOKEN, parse_mode='HTML')

conn = sqlite3.connect("database.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    added_at INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS contests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    trigger_message_id INTEGER,
    contest_message_id INTEGER,
    kind TEXT,
    meta TEXT,
    status TEXT DEFAULT 'awaiting',
    created_at INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id INTEGER,
    user_id INTEGER,
    nickname TEXT,
    joined_at INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS voice_votes (
    contest_id INTEGER,
    voter_id INTEGER,
    target_nickname TEXT,
    UNIQUE(contest_id, voter_id)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id INTEGER,
    referrer_id INTEGER,
    invited_user_id INTEGER,
    created_at INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS batl_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id INTEGER,
    user_id INTEGER,
    post_message_id INTEGER,
    chat_id INTEGER,
    nickname TEXT
)
""")

conn.commit()

admin_state = {}

def save_user(user):
    uid = user.id
    username = getattr(user, "username", "") or ""
    first = getattr(user, "first_name", "") or ""
    now = int(time.time())
    cur.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, added_at) VALUES (?, ?, ?, ?)",
                (uid, username, first, now))
    conn.commit()

def contest_type_markup():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎤 Ovozli konkurs", callback_data="type_voice"))
    kb.add(types.InlineKeyboardButton("🔗 Taklif havolali konkurs", callback_data="type_referral"))
    kb.add(types.InlineKeyboardButton("⚔️ Batl konkursi", callback_data="type_batl"))
    kb.add(types.InlineKeyboardButton("🎲 Random konkurs", callback_data="type_random"))
    return kb

def join_markup(contest_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Qatnashish", callback_data=f"join_{contest_id}"))
    return kb

@bot.message_handler(commands=['start'])
def handle_start(m):
    save_user(m.from_user)
    args = ""
    if m.text and len(m.text.split()) > 1:
        args = m.text.split(maxsplit=1)[1]
    if args and args.startswith("ref"):
        try:
            payload = args[3:]
            parts = payload.split("_")
            contest_id = int(parts[0])
            referrer_id = int(parts[1])
            cur.execute("SELECT invited_user_id FROM referrals WHERE contest_id=? AND invited_user_id=?",
                        (contest_id, m.from_user.id))
            if not cur.fetchone() and m.from_user.id != referrer_id:
                cur.execute("INSERT INTO referrals (contest_id, referrer_id, invited_user_id, created_at) VALUES (?, ?, ?, ?)",
                            (contest_id, referrer_id, m.from_user.id, int(time.time())))
                conn.commit()
                try:
                    bot.send_message(referrer_id, f"✅ @{m.from_user.username or m.from_user.first_name} sizning havolangiz orqali a'zo bo'ldi!")
                except Exception:
                    pass
        except Exception:
            pass
    if m.from_user.id == ADMIN_ID:
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
               types.InlineKeyboardButton("📣 Reklama yuborish", callback_data="admin_ad"))
        bot.send_message(m.chat.id, "👋 Salom, admin! Admin panel:", reply_markup=kb)
    else:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📖 Qoidalar", callback_data="show_rules"))
        kb.add(types.InlineKeyboardButton("📢 Kanalga o'tish", url=f"https://t.me/{BOT_USERNAME.lstrip('@')}"))
        bot.send_message(m.chat.id, "🎉 Salom! Bu bot orqali konkurslarda qatnashishingiz mumkin. Qoidalarni o'qish uchun tugmani bosing.", reply_markup=kb)

@bot.channel_post_handler(func=lambda m: True)
def handle_channel_post(post):
    text = (post.text or post.caption or "").lower()
    if any(k in text for k in TRIGGER_KEYWORDS):
        now = int(time.time())
        cur.execute("INSERT INTO contests (chat_id, trigger_message_id, kind, meta, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (post.chat.id, post.message_id, "awaiting", json.dumps({}), "awaiting_type", now))
        conn.commit()
        reply_text = f"🧾 Konkurs turlarini tanlang\nBot: {BOT_USERNAME}"
        bot.send_message(post.chat.id, reply_text, reply_to_message_id=post.message_id, reply_markup=contest_type_markup())

@bot.callback_query_handler(func=lambda cb: cb.data and cb.data.startswith("type_"))
def type_selected(cb):
    cb.answer()
    kind_map = {"type_voice": "voice", "type_referral": "referral", "type_batl": "batl", "type_random": "random"}
    chosen = kind_map.get(cb.data, "voice")
    chat_id = cb.message.chat.id
    cur.execute("SELECT id, trigger_message_id FROM contests WHERE chat_id=? AND status='awaiting_type' ORDER BY created_at DESC LIMIT 1", (chat_id,))
    row = cur.fetchone()
    if not row:
        bot.send_message(cb.message.chat.id, "🔎 Sozlanadigan konkurs topilmadi.")
        return
    contest_id, trigger_msg_id = row
    if chosen == "random":
        cur.execute("UPDATE contests SET kind=?, status='configuring' WHERE id=?", (chosen, contest_id))
        conn.commit()
        bot.send_message(cb.message.chat.id, "🎲 Random konkurs tanlandi. Admin botga DMda quyidagi formatda yozsin:\nTavsif | max_participants | winners_count | @channel(optional)")
        try:
            bot.send_message(ADMIN_ID, "Random konkurs sozlash tayyor. Format:\nTavsif | max_participants | winners_count | @channel(optional)")
        except Exception:
            bot.send_message(cb.message.chat.id, "Adminga DM yuborilmadi, admin bot bilan DM ochsin.")
        return
    if chosen == "voice":
        post_text = "<b>🎤 Ovozli konkurs</b>\n\nIshtirok etish uchun pastdagi tugmani bosing. Har bir foydalanuvchi faqat 1 marta ishtirok etadi.\nFaqat kanal a'zolari ovoz bera oladi."
    elif chosen == "referral":
        post_text = "<b>🔗 Taklif havolali konkurs</b>\n\nQo'shiling va o'z taklif havolangizni ulashing. Har bir yangi a'zo sizga ball olib keladi."
    else:
        post_text = "<b>⚔️ Batl konkursi</b>\n\nQatnashish tugmasini bosing — har bir qatnashchi uchun kanalga alohida post yaratiladi."
    sent = bot.send_message(chat_id, post_text, reply_to_message_id=trigger_msg_id)
    bot.send_message(chat_id, "Ishtirok etish uchun:", reply_to_message_id=sent.message_id, reply_markup=join_markup(contest_id))
    cur.execute("UPDATE contests SET contest_message_id=?, kind=?, meta=?, status='active' WHERE id=?", (sent.message_id, chosen, json.dumps({}), contest_id))
    conn.commit()
    bot.send_message(cb.message.chat.id, "✅ Konkurs kanalda e'lon qilindi.")

@bot.callback_query_handler(func=lambda cb: cb.data and cb.data.startswith("join_"))
def join_handler(cb):
    cb.answer()
    try:
        cid = int(cb.data.split("_", 1)[1])
    except Exception:
        return
    user = cb.from_user
    cur.execute("SELECT chat_id, contest_message_id, kind, meta, status FROM contests WHERE id=?", (cid,))
    row = cur.fetchone()
    if not row:
        bot.send_message(cb.message.chat.id, "Konkurs topilmadi yoki bekor qilingan.")
        return
    chat_id, contest_msg_id, kind, meta_s, status = row
    meta = json.loads(meta_s) if meta_s else {}
    if kind == "voice":
        cur.execute("SELECT 1 FROM voice_votes WHERE contest_id=? AND voter_id=?", (cid, user.id))
        if cur.fetchone():
            try:
                bot.answer_callback_query(cb.id, "⚠️ Siz allaqachon ovoz bergansiz!", show_alert=True)
            except:
                pass
            return
        nickname = user.username or user.first_name
        cur.execute("INSERT INTO participants (contest_id, user_id, nickname, joined_at) VALUES (?, ?, ?, ?)",
                    (cid, user.id, nickname, int(time.time())))
        conn.commit()
        cur.execute("SELECT nickname FROM participants WHERE contest_id=?", (cid,))
        names = cur.fetchall()
        updated = "<b>🎤 Ovozli konkurs</b>\n\n🗳 Ishtirokchilar:\n"
        for n in names:
            updated += f"• {n[0]}\n"
        updated += "\nHar bir ishtirokchi ustiga bosib ovoz bering."
        try:
            bot.edit_message_text(updated, chat_id, contest_msg_id, parse_mode='HTML')
        except Exception:
            pass
        bot.send_message(chat_id, f"✅ @{user.username or user.first_name} qatnashuvga qo'shildi!")
        return
    if kind == "referral":
        cur.execute("SELECT 1 FROM participants WHERE contest_id=? AND user_id=?", (cid, user.id))
        if cur.fetchone():
            try:
                bot.answer_callback_query(cb.id, "Siz allaqachon qatnashgansiz.", show_alert=True)
            except:
                pass
            return
        nickname = user.username or user.first_name
        cur.execute("INSERT INTO participants (contest_id, user_id, nickname, joined_at) VALUES (?, ?, ?, ?)",
                    (cid, user.id, nickname, int(time.time())))
        conn.commit()
        payload = f"ref{cid}_{user.id}"
        ref_link = f"https://t.me/{BOT_USERNAME.lstrip('@')}?start={payload}"
        try:
            bot.send_message(user.id, f"Sizning taklif havolangiz:\n{ref_link}\nUshbu havola orqali a'zo bo'lganlar sizga ball beradi.")
        except Exception:
            pass
        bot.send_message(chat_id, f"✅ @{user.username or user.first_name} taklif havolasi olindi.")
        return
    if kind == "batl":
        cur.execute("SELECT COUNT(*) FROM batl_posts WHERE contest_id=?", (cid,))
        cnt = cur.fetchone()[0] or 0
        participant_no = cnt + 1
        nickname = user.username or user.first_name
        batl_text = f"🥊 {participant_no}- ishtirokchi\n{nickname}\n\n❤️ Reaksiya — 1 ball\n⭐ Stars — 3 ball\n🚀 Boost — 5 ball\nBoost uchun adminga yozing"
        try:
            sent = bot.send_message(chat_id, batl_text)
            cur.execute("INSERT INTO batl_posts (contest_id, user_id, post_message_id, chat_id, nickname) VALUES (?, ?, ?, ?, ?)",
                        (cid, user.id, sent.message_id, chat_id, nickname))
            conn.commit()
            bot.send_message(chat_id, f"✅ @{user.username or user.first_name} batlga qo'shildi.")
        except Exception:
            bot.send_message(chat_id, "Xatolik yuz berdi — admin bilan bog'laning.")
        return
    if kind == "random":
        cur.execute("SELECT meta FROM contests WHERE id=?", (cid,))
        meta_s = cur.fetchone()[0] or "{}"
        meta = json.loads(meta_s)
        maxp = int(meta.get("max_participants", 0)) or 0
        cur.execute("SELECT 1 FROM participants WHERE contest_id=? AND user_id=?", (cid, user.id))
        if cur.fetchone():
            try:
                bot.answer_callback_query(cb.id, "Siz allaqachon qatnashgansiz.", show_alert=True)
            except:
                pass
            return
        cur.execute("INSERT INTO participants (contest_id, user_id, nickname, joined_at) VALUES (?, ?, ?, ?)",
                    (cid, user.id, user.username or user.first_name, int(time.time())))
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM participants WHERE contest_id=?", (cid,))
        current = cur.fetchone()[0] or 0
        bot.send_message(user.id, f"✅ Qabul qilindingiz. Hozirgi qatnashchilar: {current}/{maxp if maxp else '—'}")
        if maxp and current >= maxp:
            cur.execute("SELECT user_id FROM participants WHERE contest_id=?", (cid,))
            rows = cur.fetchall()
            user_ids = [r[0] for r in rows]
            winners_count = int(meta.get("winners", 1))
            winners = random.sample(user_ids, k=min(winners_count, len(user_ids)))
            text = "<b>🎉 Random konkurs yakunlandi!</b>\n\nG'oliblar:\n"
            for i, uid in enumerate(winners, start=1):
                try:
                    memb = bot.get_chat_member(chat_id, uid)
                    nick = f"@{memb.user.username}" if memb.user.username else memb.user.first_name
                except Exception:
                    nick = str(uid)
                text += f"{i}. {nick}\n"
            bot.send_message(chat_id, text)
            cur.execute("UPDATE contests SET status='finished' WHERE id=?", (cid,))
            conn.commit()
        return
    bot.send_message(cb.message.chat.id, "Bu konkurs turi hali to'liq qo'llab-quvvatlanmaydi.")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and "|" in (m.text or ""))
def admin_random_config(m):
    text = m.text.strip()
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 3:
        bot.reply_to(m, "Iltimos format: Tavsif | max_participants | winners_count | @channel (optional)")
        return
    desc = parts[0]
    try:
        max_participants = int(parts[1])
        winners = int(parts[2])
    except ValueError:
        bot.reply_to(m, "Iltimos, max_participants va winners sonini butun son sifatida kiriting.")
        return
    channel = parts[3] if len(parts) >= 4 else None
    cur.execute("SELECT id, chat_id, trigger_message_id FROM contests WHERE status='configuring' ORDER BY created_at DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        bot.reply_to(m, "Sozlanayotgan konfiguratsiya topilmadi.")
        return
    contest_id, chat_id, trigger_msg_id = row
    meta = {"description": desc, "max_participants": max_participants, "winners": winners, "channel": channel}
    cur.execute("UPDATE contests SET meta=?, status='active', kind='random' WHERE id=?", (json.dumps(meta), contest_id))
    conn.commit()
    post_text = f"<b>🎲 Random konkurs</b>\n\n{desc}\n\nMax qatnashchilar: {max_participants}\nG'oliblar soni: {winners}\n\nShartlar: Kanalga a'zo bo'lish va pastdagi tugmani bosish."
    sent = bot.send_message(chat_id, post_text, reply_to_message_id=trigger_msg_id)
    bot.send_message(chat_id, "Ishtirok etish uchun:", reply_to_message_id=sent.message_id, reply_markup=join_markup(contest_id))
    bot.reply_to(m, "Random konkurs kanalda e'lon qilindi va aktivlashtirildi.")

@bot.message_handler(commands=['stop_contest'])
def stop_contest(m):
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, "Foydalanish: /stop_contest CONTEST_ID")
        return
    try:
        cid = int(parts[1])
    except Exception:
        bot.reply_to(m, "ID butun son bo'lishi kerak.")
        return
    cur.execute("SELECT kind, chat_id, meta FROM contests WHERE id=?", (cid,))
    row = cur.fetchone()
    if not row:
        bot.reply_to(m, "Konkurs topilmadi.")
        return
    kind, chat_id, meta_s = row
    meta = json.loads(meta_s or "{}")
    cur.execute("SELECT user_id FROM participants WHERE contest_id=?", (cid,))
    rows = cur.fetchall()
    user_ids = [r[0] for r in rows]
    winners = []
    if user_ids:
        winners_count = int(meta.get("winners", 1)) if meta.get("winners") else 1
        winners = random.sample(user_ids, k=min(winners_count, len(user_ids)))
    text = "<b>Konkurs yakunlandi!</b>\n\n"
    if winners:
        for i, uid in enumerate(winners, start=1):
            try:
                memb = bot.get_chat_member(chat_id, uid)
                nick = f"@{memb.user.username}" if memb.user.username else memb.user.first_name
            except Exception:
                nick = str(uid)
            text += f"{i}. {nick}\n"
    else:
        text += "G'oliblar topilmadi."
    try:
        bot.send_message(chat_id, text)
    except Exception:
        pass
    cur.execute("UPDATE contests SET status='finished' WHERE id=?", (cid,))
    conn.commit()
    bot.reply_to(m, "Konkurs to'xtatildi va natija e'lon qilindi.")

@bot.callback_query_handler(func=lambda cb: cb.data == "admin_stats")
def admin_stats(cb):
    cb.answer()
    if cb.from_user.id != ADMIN_ID:
        try:
            bot.answer_callback_query(cb.id, "Faqat admin", show_alert=True)
        except:
            pass
        return
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM contests")
    total_contests = cur.fetchone()[0] or 0
    bot.send_message(cb.message.chat.id, f"📊 Statistika:\nFoydalanuvchilar: {total_users}\nKonkurslar: {total_contests}")

@bot.callback_query_handler(func=lambda cb: cb.data == "admin_ad")
def admin_ad(cb):
    cb.answer()
    if cb.from_user.id != ADMIN_ID:
        try:
            bot.answer_callback_query(cb.id, "Faqat admin", show_alert=True)
        except:
            pass
        return
    admin_state['awaiting_ad'] = True
    bot.send_message(cb.message.chat.id, "✍️ Reklama matnini yuboring. U barcha foydalanuvchilarga DM orqali yuboriladi.")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and admin_state.get('awaiting_ad'))
def admin_broadcast(m):
    text = m.text or ""
    if len(text) < 5:
        bot.reply_to(m, "Matn juda qisqa.")
        return
    cur.execute("SELECT user_id FROM users")
    rows = cur.fetchall()
    sent = 0
    failed = 0
    for r in rows:
        uid = r[0]
        try:
            bot.send_message(uid, f"📣 Reklama:\n\n{text}")
            sent += 1
        except Exception:
            failed += 1
    admin_state.pop('awaiting_ad', None)
    bot.reply_to(m, f"Reklama yuborildi. Yuborildi: {sent}, yuborilmadi: {failed}")

@bot.callback_query_handler(func=lambda cb: cb.data == "show_rules")
def show_rules(cb):
    cb.answer()
    bot.send_message(cb.message.chat.id, "📘 Qoidalar:\n1. Kanalga a'zo bo'ling.\n2. Qoidalarni buzish taqiqlanadi.\n3. Adolatli qatnashing.")

if __name__ == "__main__":
    bot.infinity_polling()
