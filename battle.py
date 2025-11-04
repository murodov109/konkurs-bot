from telebot import TeleBot, types

bot = TeleBot("TOKENINGNI_BU_YERGA_QOY")

battle_data = {
    "participants": [],
    "posts": {},
    "scores": {}
}

def handle_battle_konkurs(message):
    chat_id = message.chat.id
    text = "⚔️ Batl konkursi boshlandi!\n\n💡 Qatnashmoqchimisiz? Tugmani bosing.\n👇"
    markup = types.InlineKeyboardMarkup()
    join_btn = types.InlineKeyboardButton("🗡️ Qatnashish", callback_data="join_battle")
    markup.add(join_btn)
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "join_battle")
def join_battle(call):
    user = call.from_user
    user_tag = f"@{user.username}" if user.username else user.first_name
    if user.id in battle_data["participants"]:
        bot.answer_callback_query(call.id, "Siz allaqachon qatnashgansiz ⚔️")
        return
    battle_data["participants"].append(user.id)
    index = len(battle_data["participants"])
    msg = f"{index}-ishtirokchi\n{user_tag}\n\n❤️ Reaksiya — 1 ball\n⭐ Stars — 3 ball\n🚀 Boost — 5 ball\nBoost uchun adminga yozing"
    sent = bot.send_message(call.message.chat.id, msg)
    battle_data["posts"][user.id] = sent.message_id
    battle_data["scores"][user.id] = 0
    bot.answer_callback_query(call.id, "Siz muvaffaqiyatli qatnashdingiz! ⚔️")

def calculate_battle_points():
    for user_id in battle_data["participants"]:
        battle_data["scores"][user_id] += 1

def stop_battle_konkurs(message):
    chat_id = message.chat.id
    if not battle_data["participants"]:
        bot.send_message(chat_id, "⚠️ Hali hech kim qatnashmagan.")
        return
    results = "🏆 Batl yakunlandi:\n\n"
    ranking = []
    for user_id, score in battle_data["scores"].items():
        ranking.append((user_id, score))
    ranking.sort(key=lambda x: x[1], reverse=True)
    for i, (uid, score) in enumerate(ranking, start=1):
        user_tag = f"@{bot.get_chat(uid).username}" if bot.get_chat(uid).username else bot.get_chat(uid).first_name
        results += f"{i}. {user_tag} — {score} ball\n"
    bot.send_message(chat_id, results)
    battle_data["participants"].clear()
    battle_data["posts"].clear()
    battle_data["scores"].clear()
