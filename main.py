from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import sqlite3
import json
import random
import logging

BOT_TOKEN = "8452391283:AAESGiQ0GClTdX8aElJonmj3194lpNin00M"
ADMIN_ID = 7617397626
BOT_USERNAME = "@unversal_konkurs_bot"
TRIGGER_KEYWORDS = ["#konkurs", "!konkurs", "!startcontest"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

DB_PATH = "database.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS contests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    trigger_message_id INTEGER,
    contest_message_id INTEGER,
    kind TEXT,
    meta TEXT,
    status TEXT DEFAULT 'awaiting',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id INTEGER,
    user_id INTEGER,
    nickname TEXT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS voice_votes (
    contest_id INTEGER,
    voter_id INTEGER,
    target_nickname TEXT,
    UNIQUE(contest_id, voter_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id INTEGER,
    referrer_id INTEGER,
    invited_user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
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

def save_user(user: types.User):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                   (user.id, user.username or "", user.first_name or ""))
    conn.commit()

def contest_type_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🎤 Ovozli konkurs", callback_data="type_voice"),
        InlineKeyboardButton("🔗 Taklif havolali konkurs", callback_data="type_referral"),
        InlineKeyboardButton("⚔️ Batl konkursi", callback_data="type_batl"),
        InlineKeyboardButton("🎲 Random konkurs", callback_data="type_random")
    )
    return kb

def join_button(contest_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Qatnashish", callback_data=f"join_{contest_id}"))
    return kb

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    save_user(message.from_user)
    args = message.get_args()
    if args and args.startswith("ref"):
        try:
            payload = args[3:]
            parts = payload.split("_")
            contest_id = int(parts[0])
            referrer_id = int(parts[1])
            cursor.execute("SELECT invited_user_id FROM referrals WHERE contest_id=? AND invited_user_id=?", (contest_id, message.from_user.id))
            if not cursor.fetchone() and message.from_user.id != referrer_id:
                cursor.execute("INSERT INTO referrals (contest_id, referrer_id, invited_user_id) VALUES (?, ?, ?)",
                               (contest_id, referrer_id, message.from_user.id))
                conn.commit()
                try:
                    await bot.send_message(referrer_id, f"✅ @{message.from_user.username or message.from_user.first_name} sizning havolangiz orqali a'zo bo'ldi!")
                except Exception:
                    pass
        except Exception as e:
            logger.warning("Referral parse error: %s", e)

    if message.from_user.id == ADMIN_ID:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton("📣 Reklama yuborish", callback_data="admin_ad")
        )
        await message.answer("👋 Salom, admin! Admin panel:", reply_markup=kb)
    else:
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("📖 Qoidalar", callback_data="show_rules"))
        kb.add(InlineKeyboardButton("📢 Kanalga o'tish", url=f"https://t.me/{BOT_USERNAME.lstrip('@')}"))
        await message.answer("🎉 Salom! Bu bot orqali konkurslarda qatnashishingiz mumkin. Qoidalarni o'qish uchun tugmani bosing.", reply_markup=kb)

@dp.channel_post_handler()
async def on_channel_post(post: types.Message):
    text = (post.text or post.caption or "").lower()
    if any(k in text for k in TRIGGER_KEYWORDS):
        cursor.execute("INSERT INTO contests (chat_id, trigger_message_id, kind, meta, status) VALUES (?, ?, ?, ?, ?)",
                       (post.chat.id, post.message_id, "awaiting", json.dumps({}), "awaiting_type"))
        conn.commit()
        reply_text = f"🧾 Konkurs turlarini tanlang\nBot: {BOT_USERNAME}"
        await bot.send_message(post.chat.id, reply_text, reply_to_message_id=post.message_id, reply_markup=contest_type_keyboard())

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("type_"))
async def on_type_selected(callback: types.CallbackQuery):
    await callback.answer()
    kind_map = {
        "type_voice": "voice",
        "type_referral": "referral",
        "type_batl": "batl",
        "type_random": "random"
    }
    chosen_kind = kind_map.get(callback.data, "voice")
    chat_id = callback.message.chat.id
    cursor.execute("SELECT id, trigger_message_id FROM contests WHERE chat_id=? AND status='awaiting_type' ORDER BY created_at DESC LIMIT 1", (chat_id,))
    row = cursor.fetchone()
    if not row:
        await callback.message.reply("🔎 Sozlanadigan konkurs topilmadi.")
        return
    contest_id, trigger_msg_id = row
    if chosen_kind == "random":
        cursor.execute("UPDATE contests SET kind=?, status='configuring' WHERE id=?", (chosen_kind, contest_id))
        conn.commit()
        await callback.message.reply("🎲 Random konkurs tanlandi. Admin, bot DMga o'ting va quyidagi ma'lumotlarni bering:\nTavsif, maksimal qatnashchilar, g'oliblar soni, (ixtiyoriy) kanal username\nFormat: Tavsif | 100 | 3 | @kanal")
        try:
            await bot.send_message(ADMIN_ID, f"Random konkurs sozlash uchun yangi element tayyor. Iltimos admin sifatida quyidagi formatda javob bering:\nTavsif | max_participants | winners_count | @channel (optional)\nMasalan:\n<i>iPhone sovg'a | 100 | 3 | @kanal</i>")
        except Exception:
            await callback.message.reply("Adminga DM yuborib bo'lmadi — admin bot bilan DM ochsin.")
        return
    meta = {}
    if chosen_kind == "voice":
        post_text = ("<b>🎤 Ovozli konkurs</b>\n\n"
                     "Ishtirok etish uchun pastdagi tugmani bosing. Har bir foydalanuvchi faqat 1 marta ishtiroketa oladi.\n"
                     "Faqat kanal a'zolari ovoz bera oladi.")
    elif chosen_kind == "referral":
        post_text = ("<b>🔗 Taklif havolali konkurs</b>\n\n"
                     "Qo'shiling va o'z taklif havolangizni ulashing. Har bir yangi a'zo sizga ball olib keladi.")
        meta = {"note": "referral"}
    else:
        post_text = ("<b>⚔️ Batl konkursi</b>\n\n"
                     "Qatnashish tugmasini bosing — har bir qatnashchi uchun kanalga alohida post yaratiladi.")
    sent = await bot.send_message(chat_id, post_text, reply_to_message_id=trigger_msg_id)
    await bot.send_message(chat_id, "Ishtirok etish uchun:", reply_to_message_id=sent.message_id, reply_markup=join_button(contest_id))
    cursor.execute("UPDATE contests SET contest_message_id=?, kind=?, meta=?, status='active' WHERE id=?",
                   (sent.message_id, chosen_kind, json.dumps(meta), contest_id))
    conn.commit()
    await callback.message.reply("✅ Konkurs kanalda e'lon qilindi.")

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("join_"))
async def on_join(callback: types.CallbackQuery):
    await callback.answer()
    parts = callback.data.split("_", 1)
    if len(parts) < 2:
        return
    cid = int(parts[1])
    user = callback.from_user
    cursor.execute("SELECT chat_id, contest_message_id, kind, meta, status FROM contests WHERE id=?", (cid,))
    row = cursor.fetchone()
    if not row:
        return await callback.message.reply("Konkurs topilmadi yoki bekor qilingan.")
    chat_id, contest_msg_id, kind, meta_s, status = row
    meta = json.loads(meta_s) if meta_s else {}
    if kind == "voice":
        cursor.execute("SELECT id FROM contests WHERE id=? AND kind='voice'", (cid,))
        cursor.execute("SELECT 1 FROM voice_votes WHERE contest_id=? AND voter_id=?", (cid, user.id))
        if cursor.fetchone():
            return await callback.message.answer("⚠️ Siz allaqachon ovoz bergansiz.", show_alert=True)
        cursor.execute("INSERT INTO participants (contest_id, user_id, nickname) VALUES (?, ?, ?)",
                       (cid, user.id, user.username or user.full_name))
        conn.commit()
        cursor.execute("SELECT nickname FROM participants WHERE contest_id=?", (cid,))
        names = cursor.fetchall()
        updated_text = "<b>🎤 Ovozli konkurs</b>\n\n🗳 Ishtirokchilar:\n"
        for n in names:
            updated_text += f"• {n[0]}\n"
        updated_text += "\nHar bir ishtirokchi ustiga bosib ovoz bering (keyin ovoz funksiyasi qo'shiladi)."
        try:
            await bot.edit_message_text(updated_text, chat_id=chat_id, message_id=contest_msg_id)
        except Exception:
            pass
        await callback.message.answer("✅ Siz qatnashdingiz.")
        return
    if kind == "referral":
        cursor.execute("SELECT 1 FROM participants WHERE contest_id=? AND user_id=?", (cid, user.id))
        if cursor.fetchone():
            return await callback.message.answer("Siz allaqachon qatnashgansiz.")
        nickname = user.username or user.full_name
        cursor.execute("INSERT INTO participants (contest_id, user_id, nickname) VALUES (?, ?, ?)", (cid, user.id, nickname))
        conn.commit()
        payload = f"ref{cid}_{user.id}"
        ref_link = f"https://t.me/{BOT_USERNAME.lstrip('@')}?start={payload}"
        try:
            await bot.send_message(user.id, f"Sizning taklif havolangiz:\n{ref_link}\nUshbu havola orqali a'zo bo'lganlar sizga ball beradi.")
        except Exception:
            pass
        await callback.message.answer("✅ Siz muvaffaqiyatli qo'shildingiz. Taklif havolasi DMga yuborildi.")
        return
    if kind == "batl":
        cursor.execute("SELECT contest_message_id FROM contests WHERE id=?", (cid,))
        contest_msg = cursor.fetchone()
        if not contest_msg:
            return await callback.message.answer("Konkurs topilmadi.")
        nickname = user.username or user.full_name
        cursor.execute("SELECT COUNT(*) FROM batl_posts WHERE contest_id=?", (cid,))
        cnt = cursor.fetchone()[0] or 0
        participant_no = cnt + 1
        batl_text = (
            f"🥊 {participant_no}- ishtirokchi\n"
            f"{nickname}\n\n"
            "❤️ Reaksiya — 1 ball\n"
            "⭐ Stars — 3 ball\n"
            "🚀 Boost — 5 ball\n"
            "Boost uchun adminga yozing"
        )
        try:
            sent = await bot.send_message(chat_id, batl_text)
            cursor.execute("INSERT INTO batl_posts (contest_id, user_id, post_message_id, chat_id, nickname) VALUES (?, ?, ?, ?, ?)",
                           (cid, user.id, sent.message_id, chat_id, nickname))
            conn.commit()
            await callback.message.answer("✅ Siz batlga qo'shildingiz va post yaratildi.")
        except Exception as e:
            logger.warning("Failed to post batl entry: %s", e)
            await callback.message.answer("Xatolik yuz berdi — admin bilan bog'laning.")
        return
    if kind == "random":
        cursor.execute("SELECT meta FROM contests WHERE id=?", (cid,))
        meta_s = cursor.fetchone()[0] or "{}"
        meta = json.loads(meta_s)
        maxp = int(meta.get("max_participants", 0)) or 0
        cursor.execute("SELECT 1 FROM participants WHERE contest_id=? AND user_id=?", (cid, user.id))
        if cursor.fetchone():
            return await callback.message.answer("Siz allaqachon qatnashgansiz.")
        cursor.execute("INSERT INTO participants (contest_id, user_id, nickname) VALUES (?, ?, ?)",
                       (cid, user.id, user.username or user.full_name))
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM participants WHERE contest_id=?", (cid,))
        current = cursor.fetchone()[0] or 0
        await callback.message.answer(f"✅ Qabul qilindingiz. Hozirgi qatnashchilar: {current}/{maxp if maxp else '—'}")
        if maxp and current >= maxp:
            cursor.execute("SELECT user_id FROM participants WHERE contest_id=?", (cid,))
            rows = cursor.fetchall()
            user_ids = [r[0] for r in rows]
            winners_count = int(meta.get("winners", 1))
            winners = random.sample(user_ids, k=min(winners_count, len(user_ids)))
            text = "<b>🎉 Random konkurs yakunlandi!</b>\n\nG'oliblar:\n"
            for i, uid in enumerate(winners, start=1):
                try:
                    member = await bot.get_chat_member(chat_id, uid)
                    nick = f"@{member.user.username}" if member.user.username else member.user.full_name
                except Exception:
                    nick = str(uid)
                text += f"{i}. {nick}\n"
            await bot.send_message(chat_id, text)
            cursor.execute("UPDATE contests SET status='finished' WHERE id=?", (cid,))
            conn.commit()
        return
    await callback.message.answer("Bu konkurs turi hali to'liq qo'llab-quvvatlanmaydi.")

@dp.message_handler(lambda m: m.from_user.id == ADMIN_ID and "|" in (m.text or ""))
async def admin_random_config(m: types.Message):
    text = m.text.strip()
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 3:
        await m.reply("Iltimos format: Tavsif | max_participants | winners_count | @channel (optional)")
        return
    desc = parts[0]
    try:
        max_participants = int(parts[1])
        winners = int(parts[2])
    except ValueError:
        await m.reply("Iltimos, max_participants va winners sonini butun son sifatida kiriting.")
        return
    channel = parts[3] if len(parts) >= 4 else None
    cursor.execute("SELECT id, chat_id, trigger_message_id FROM contests WHERE status='configuring' ORDER BY created_at DESC LIMIT 1")
    row = cursor.fetchone()
    if not row:
        await m.reply("Sozlanayotgan konfiguratsiya topilmadi.")
        return
    contest_id, chat_id, trigger_msg_id = row
    meta = {"description": desc, "max_participants": max_participants, "winners": winners, "channel": channel}
    cursor.execute("UPDATE contests SET meta=?, status='active', kind='random' WHERE id=?", (json.dumps(meta), contest_id))
    conn.commit()
    post_text = f"<b>🎲 Random konkurs</b>\n\n{desc}\n\nMax qatnashchilar: {max_participants}\nG'oliblar soni: {winners}\n\nShartlar: Kanalga a'zo bo'lish va pastdagi tugmani bosish."
    sent = await bot.send_message(chat_id, post_text, reply_to_message_id=trigger_msg_id)
    await bot.send_message(chat_id, "Ishtirok etish uchun:", reply_to_message_id=sent.message_id, reply_markup=join_button(contest_id))
    await m.reply("Random konkurs kanalda e'lon qilindi va aktivlashtirildi.")

@dp.message_handler(commands=["stop_contest"])
async def stop_contest_cmd(m: types.Message):
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) < 2:
        await m.reply("Foydalanish: /stop_contest CONTEST_ID")
        return
    try:
        cid = int(parts[1])
    except ValueError:
        await m.reply("ID butun son bo'lishi kerak.")
        return
    cursor.execute("SELECT kind, chat_id, meta FROM contests WHERE id=?", (cid,))
    row = cursor.fetchone()
    if not row:
        await m.reply("Konkurs topilmadi.")
        return
    kind, chat_id, meta_s = row
    meta = json.loads(meta_s or "{}")
    cursor.execute("SELECT user_id FROM participants WHERE contest_id=?", (cid,))
    rows = cursor.fetchall()
    user_ids = [r[0] for r in rows]
    winners = []
    if user_ids:
        winners_count = int(meta.get("winners", 1)) if meta.get("winners") else 1
        winners = random.sample(user_ids, k=min(winners_count, len(user_ids)))
    text = "<b>Konkurs yakunlandi!</b>\n\n"
    if winners:
        for i, uid in enumerate(winners, start=1):
            try:
                member = await bot.get_chat_member(chat_id, uid)
                nick = f"@{member.user.username}" if member.user.username else member.user.full_name
            except Exception:
                nick = str(uid)
            text += f"{i}. {nick}\n"
    else:
        text += "G'oliblar topilmadi."
    try:
        await bot.send_message(chat_id, text)
    except Exception:
        pass
    cursor.execute("UPDATE contests SET status='finished' WHERE id=?", (cid,))
    conn.commit()
    await m.reply("Konkurs to'xtatildi va natija e'lon qilindi.")

@dp.callback_query_handler(lambda c: c.data == "admin_stats")
async def admin_stats_cb(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Faqat admin", show_alert=True)
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM contests")
    total_contests = cursor.fetchone()[0] or 0
    await callback.message.answer(f"📊 Statistika:\nFoydalanuvchilar: {total_users}\nKonkurslar: {total_contests}")

@dp.callback_query_handler(lambda c: c.data == "admin_ad")
async def admin_ad_cb(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Faqat admin", show_alert=True)
    await callback.message.answer("✍️ Reklama matnini kiriting. U barcha foydalanuvchilarga DM orqali yuboriladi.")

@dp.message_handler(lambda m: m.from_user.id == ADMIN_ID and m.reply_to_message is None)
async def admin_ad_broadcast(m: types.Message):
    text = m.text or ""
    if len(text) < 5:
        return
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    sent = 0
    failed = 0
    for r in rows:
        uid = r[0]
        try:
            await bot.send_message(uid, f"📣 Reklama:\n\n{text}")
            sent += 1
        except Exception:
            failed += 1
    await m.reply(f"Reklama yuborildi. Yuborildi: {sent}, yuborilmadi: {failed}")

@dp.callback_query_handler(lambda c: c.data == "show_rules")
async def show_rules_cb(callback: types.CallbackQuery):
    await callback.message.answer("📘 Qoidalar:\n1. Kanalga a'zo bo'ling.\n2. Qoidalarni buzish taqiqlanadi.\n3. Adolatli qatnashing.")

async def on_shutdown(dp):
    await bot.session.close()
    conn.close()

if __name__ == "__main__":
    try:
        logger.info("Bot starting...")
        executor.start_polling(dp, skip_updates=True, on_shutdown=on_shutdown)
    except Exception as e:
        logger.exception("Bot stopped with exception: %s", e)
