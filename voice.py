from telebot import TeleBot, types

bot = None
voice_contests = {}

def init_voice_module(bot_instance):
    global bot
    bot = bot_instance

def handle_voice_konkurs(message):
    chat_id = message.chat.id
    text = (
        "🎤 Ovozli konkurs boshlandi!\n"
        "Foydalanuvchilar ovoz berish orqali qatnashadilar.\n\n"
        "👇 Quyidagi tugmalar orqali ovoz bering:"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔊 Ovoz berish", callback_data=f"vote_voice_{chat_id}"),
        types.InlineKeyboardButton("📊 Natijalar", callback_data=f"results_voice_{chat_id}")
    )

    sent = bot.send_message(chat_id, text, reply_markup=markup)
    voice_contests[chat_id] = {"message_id": sent.message_id, "votes": {}}

def handle_vote_callback(call):
    data = call.data
    user_id = call.from_user.id

    if not data.startswith("vote_voice_"):
        return

    chat_id = int(data.split("_")[-1])
    if chat_id not in voice_contests:
        bot.answer_callback_query(call.id, "❌ Bu konkurs topilmadi.")
        return

    contest = voice_contests[chat_id]
    if user_id in contest["votes"]:
        bot.answer_callback_query(call.id, "✅ Siz allaqachon ovoz bergansiz.")
    else:
        contest["votes"][user_id] = True
        bot.answer_callback_query(call.id, "🎤 Ovoz qabul qilindi!")

def handle_results_callback(call):
    data = call.data
    if not data.startswith("results_voice_"):
        return

    chat_id = int(data.split("_")[-1])
    if chat_id not in voice_contests:
        bot.answer_callback_query(call.id, "❌ Natijalar topilmadi.")
        return

    votes = len(voice_contests[chat_id]["votes"])
    bot.answer_callback_query(call.id)
    bot.send_message(chat_id, f"📊 Hozircha ovozlar soni: {votes}")

def stop_voice_konkurs(message):
    chat_id = message.chat.id
    if chat_id not in voice_contests:
        bot.send_message(chat_id, "❌ Aktiv konkurs topilmadi.")
        return

    votes = len(voice_contests[chat_id]["votes"])
    bot.send_message(chat_id, f"🏁 Konkurs yakunlandi!\nUmumiy ovozlar: {votes}")
    del voice_contests[chat_id]

def register_voice_handlers(bot_instance):
    init_voice_module(bot_instance)
    bot_instance.callback_query_handler(func=lambda call: call.data.startswith("vote_voice_"))(handle_vote_callback)
    bot_instance.callback_query_handler(func=lambda call: call.data.startswith("results_voice_"))(handle_results_callback)
