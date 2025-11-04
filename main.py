BOT_TOKEN = "8452391283:AAESGiQ0GClTdX8aElJonmj3194lpNin00M"
from telebot import TeleBot, types
from voice import handle_voice_konkurs, stop_voice_konkurs
from link import handle_link_konkurs, stop_link_konkurs
from battle import handle_battle_konkurs, stop_battle_konkurs

TOKEN = "8452391283:AAESGiQ0GClTdX8aElJonmj3194lpNin00M"
ADMIN_ID = 7617397626
bot = TeleBot(TOKEN, parse_mode="HTML")

def main_menu(chat_id):
    text = "📢 Kanallar uchun kerakli buyruqlar ro'yxati 📜\n\n1. #konkurs — kanalga yuborsangiz 3 xil konkurs (ovozli, havolali, batl)\n2. #konkurs_stop — konkursni to'xtatish\n3. #konkurs_off — tugmalarni o'chirish\n\nBotdan foydalanish uchun kanalga admin sifatida qo'shing."
    markup = types.InlineKeyboardMarkup()
    add_btn = types.InlineKeyboardButton("➕ Kanalga qo‘shish", url="https://t.me/unversal_konkurs_bot?startchannel")
    markup.add(add_btn)
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        admin_panel(message)
    else:
        main_menu(message.chat.id)

def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📈 Statistika", "📢 Reklama yuborish")
    markup.row("🏁 Konkurslar ro‘yxati")
    bot.send_message(message.chat.id, "👑 Admin paneliga xush kelibsiz!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📈 Statistika" and m.from_user.id == ADMIN_ID)
def show_stats(message):
    bot.send_message(message.chat.id, "📊 Statistika: foydalanuvchilar soni va faoliyat hisoblanmoqda...")

@bot.message_handler(func=lambda m: m.text == "📢 Reklama yuborish" and m.from_user.id == ADMIN_ID)
def send_ad(message):
    bot.send_message(message.chat.id, "✉️ Reklama matnini yuboring.")
    bot.register_next_step_handler(message, broadcast_message)

def broadcast_message(message):
    bot.send_message(message.chat.id, "📨 Reklama yuborildi (demo versiya).")

@bot.message_handler(func=lambda m: m.text == "🏁 Konkurslar ro‘yxati" and m.from_user.id == ADMIN_ID)
def konkurs_list(message):
    bot.send_message(message.chat.id, "🎯 Mavjud konkurslar:\n1. Ovozli konkurs\n2. Taklif havolali konkurs\n3. Batl konkursi")

@bot.message_handler(func=lambda message: message.text and "#konkurs" in message.text)
def konkurs_start(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🎤 Ovozli konkurs", callback_data="konkurs_voice")
    btn2 = types.InlineKeyboardButton("🔗 Taklif havolali", callback_data="konkurs_link")
    btn3 = types.InlineKeyboardButton("⚔️ Batl konkursi", callback_data="konkurs_battle")
    markup.add(btn1, btn2, btn3)
    bot.reply_to(message, "🔰 Qaysi turdagi konkursni boshlaymiz?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["konkurs_voice", "konkurs_link", "konkurs_battle"])
def konkurs_choice(call):
    if call.data == "konkurs_voice":
        handle_voice_konkurs(call.message)
    elif call.data == "konkurs_link":
        handle_link_konkurs(call.message)
    elif call.data == "konkurs_battle":
        handle_battle_konkurs(call.message)
    bot.answer_callback_query(call.id, "Konkurs boshlandi!")

@bot.message_handler(func=lambda message: message.text and "#konkurs_stop" in message.text)
def konkurs_stop(message):
    stop_voice_konkurs(message)
    stop_link_konkurs(message)
    stop_battle_konkurs(message)
    bot.reply_to(message, "⛔ Konkurs to‘xtatildi.")

bot.infinity_polling()
