from telebot import types
import random
import string

def generate_ref_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def handle_link_konkurs(bot, message, user_data, channel_id):
    konkurs_post = bot.send_message(
        channel_id,
        "🔗 *Do‘stlarni taklif qilish konkursi boshlandi!*\n\n"
        "👉 Quyidagi tugmani bosing va o‘z taklif havolangizni oling.\n"
        "Har bir taklif qilgan do‘st uchun 1 ball qo‘shiladi!",
        parse_mode="Markdown"
    )

    markup = types.InlineKeyboardMarkup()
    join_btn = types.InlineKeyboardButton("🚀 Havolani olish", callback_data=f"get_link_{konkurs_post.message_id}")
    markup.add(join_btn)
    bot.edit_message_reply_markup(channel_id, konkurs_post.message_id, reply_markup=markup)

    user_data["link"] = {
        "refs": {},
        "points": {},
        "post_id": konkurs_post.message_id
    }

def register_link_handlers(bot, user_data, channel_id, bot_username):
    @bot.callback_query_handler(func=lambda call: call.data.startswith("get_link_"))
    def get_link(call):
        konkurs = user_data.get("link")
        if not konkurs:
            return bot.answer_callback_query(call.id, "❌ Konkurs topilmadi.")

        user_id = call.from_user.id
        username = "@" + call.from_user.username if call.from_user.username else call.from_user.first_name

        if user_id not in konkurs["refs"]:
            ref_code = generate_ref_code()
            konkurs["refs"][user_id] = ref_code
        else:
            ref_code = konkurs["refs"][user_id]

        ref_link = f"https://t.me/{bot_username}?start={ref_code}"
        bot.answer_callback_query(call.id, "Havolangiz yuborildi ✅", show_alert=False)
        bot.send_message(call.from_user.id, f"📨 Sizning taklif havolangiz:\n{ref_link}")

    @bot.message_handler(commands=['start'])
    def start_with_ref(message):
        parts = message.text.split()
        if len(parts) == 2:
            ref_code = parts[1]
            konkurs = user_data.get("link")
            if not konkurs:
                return bot.send_message(message.chat.id, "❌ Hozircha konkurs mavjud emas.")

            inviter_id = None
            for uid, code in konkurs["refs"].items():
                if code == ref_code:
                    inviter_id = uid
                    break

            if inviter_id and inviter_id != message.from_user.id:
                konkurs["points"][inviter_id] = konkurs["points"].get(inviter_id, 0) + 1
                inviter_name = konkurs["refs"].get(inviter_id, "Foydalanuvchi")
                bot.send_message(inviter_id, f"🎉 {message.from_user.first_name} sizning havolangiz orqali qo‘shildi! Ballingiz: {konkurs['points'][inviter_id]}")
        else:
            bot.send_message(
                message.chat.id,
                "👋 Salom! Bu bot orqali konkurslarda qatnashishingiz mumkin.\n"
                "Bosh menyuga qaytish uchun /menu ni bosing."
            )

def show_link_stats(bot, user_data, chat_id):
    konkurs = user_data.get("link")
    if not konkurs or not konkurs["points"]:
        return bot.send_message(chat_id, "📊 Hozircha hech kim ball to‘plamagan.")

    stats = "🏆 *Konkurs reytingi:*\n\n"
    sorted_users = sorted(konkurs["points"].items(), key=lambda x: x[1], reverse=True)
    for i, (user_id, points) in enumerate(sorted_users[:10], 1):
        stats += f"{i}. <a href='tg://user?id={user_id}'>Foydalanuvchi</a> — {points} ball\n"

    bot.send_message(chat_id, stats, parse_mode="HTML")
