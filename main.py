import telebot
from telebot import types
from voice import handle_voice_konkurs
from link import handle_link_konkurs

BOT_TOKEN = "8452391283:AAESGiQ0GClTdX8aElJonmj3194lpNin00M"
ADMIN_ID = 7617397626
CHANNEL_ID = "@YOUR_CHANNEL_USERNAME"

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

def check_user_in_channel(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

@bot.message_handler(commands=["start"])
def start(message):
    if check_user_in_channel(message.from_user.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🎤 Ovozli konkurs", "🔗 Taklifli konkurs")
        bot.send_message(message.chat.id, "Assalomu alaykum! Konkurs turini tanlang 👇", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        join_btn = types.InlineKeyboardButton("📢 Kanalga qo‘shilish", url=f"https://t.me/{CHANNEL_ID.replace('@','')}")
        check_btn = types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")
        markup.add(join_btn)
        markup.add(check_btn)
        bot.send_message(message.chat.id, "Botdan foydalanish uchun kanalga obuna bo‘ling 👇", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    if check_user_in_channel(call.from_user.id):
        bot.answer_callback_query(call.id, "Obuna tasdiqlandi ✅")
        bot.send_message(call.message.chat.id, "Endi konkurs turini tanlang 👇")
    else:
        bot.answer_callback_query(call.id, "Siz hali kanalga qo‘shilmadingiz ❗️")

@bot.message_handler(func=lambda message: message.text == "🎤 Ovozli konkurs")
def start_voice_konkurs(message):
    handle_voice_konkurs(bot, message, user_data, CHANNEL_ID)

@bot.message_handler(func=lambda message: message.text == "🔗 Taklifli konkurs")
def start_link_konkurs(message):
    handle_link_konkurs(bot, message, user_data, CHANNEL_ID)

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "Bu bo‘lim faqat bot egasi uchun 🔒")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📈 Statistika", "📢 Reklama yuborish", "♻️ Konkursni yangilash", "⬅️ Chiqish")
    bot.send_message(message.chat.id, "👑 Admin panel", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📈 Statistika" and message.from_user.id == ADMIN_ID)
def show_stats(message):
    total = len(user_data)
    active = len([u for u in user_data if user_data[u].get("active", False)])
    bot.send_message(message.chat.id, f"📊 Foydalanuvchilar: {total}\n🟢 Faollar: {active}")

@bot.message_handler(func=lambda message: message.text == "📢 Reklama yuborish" and message.from_user.id == ADMIN_ID)
def broadcast(message):
    msg = bot.send_message(message.chat.id, "Reklama matnini yuboring:")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    count = 0
    for user_id in user_data.keys():
        try:
            bot.send_message(user_id, message.text)
            count += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"✅ Reklama {count} ta foydalanuvchiga yuborildi.")

@bot.message_handler(func=lambda message: message.text == "♻️ Konkursni yangilash" and message.from_user.id == ADMIN_ID)
def reset_konkurs(message):
    user_data.clear()
    bot.send_message(message.chat.id, "🔄 Konkurs ma'lumotlari tozalandi.")

@bot.message_handler(func=lambda message: message.text == "⬅️ Chiqish" and message.from_user.id == ADMIN_ID)
def exit_admin(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Admin paneldan chiqdingiz.", reply_markup=markup)

print("✅ Bot ishga tushdi...")
bot.infinity_polling()
