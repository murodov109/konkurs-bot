from telebot import types

def handle_voice_konkurs(bot, message, user_data, channel_id):
    konkurs_post = bot.send_message(
        channel_id,
        "🎤 *Ovozli konkurs boshlandi!*\n\nQatnashish uchun pastdagi tugmani bosing 👇",
        parse_mode="Markdown"
    )

    markup = types.InlineKeyboardMarkup()
    join_btn = types.InlineKeyboardButton("🚀 Qatnashish", callback_data=f"join_voice_{konkurs_post.message_id}")
    markup.add(join_btn)
    bot.edit_message_reply_markup(channel_id, konkurs_post.message_id, reply_markup=markup)

    user_data["voice"] = {
        "participants": {},
        "votes": {},
        "post_id": konkurs_post.message_id
    }

@staticmethod
def update_voice_buttons(bot, channel_id, konkurs):
    markup = types.InlineKeyboardMarkup()
    for user_id, username in konkurs["participants"].items():
        vote_count = konkurs["votes"].get(user_id, 0)
        markup.add(types.InlineKeyboardButton(f"{username} ❤️ {vote_count}", callback_data=f"vote_{user_id}"))
    bot.edit_message_reply_markup(channel_id, konkurs["post_id"], reply_markup=markup)

def register_voice_handlers(bot, user_data, channel_id):
    @bot.callback_query_handler(func=lambda call: call.data.startswith("join_voice_"))
    def join_voice(call):
        konkurs = user_data.get("voice")
        if not konkurs:
            return bot.answer_callback_query(call.id, "❌ Konkurs topilmadi.")

        user_id = call.from_user.id
        username = "@" + call.from_user.username if call.from_user.username else call.from_user.first_name

        if user_id in konkurs["participants"]:
            return bot.answer_callback_query(call.id, "Siz allaqachon qatnashyapsiz 😉")

        konkurs["participants"][user_id] = username
        bot.answer_callback_query(call.id, "✅ Qatnashdingiz!")
        update_voice_buttons(bot, channel_id, konkurs)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("vote_"))
    def vote_user(call):
        konkurs = user_data.get("voice")
        if not konkurs:
            return bot.answer_callback_query(call.id, "❌ Konkurs topilmadi.")

        voter = call.from_user.id
        voted_id = int(call.data.split("_")[1])

        if voter == voted_id:
            return bot.answer_callback_query(call.id, "O‘zingizga ovoz bera olmaysiz 😂")

        if "voted_by" not in konkurs:
            konkurs["voted_by"] = {}
        if voter in konkurs["voted_by"]:
            return bot.answer_callback_query(call.id, "Siz allaqachon ovoz bergansiz!")

        konkurs["voted_by"][voter] = voted_id
        konkurs["votes"][voted_id] = konkurs["votes"].get(voted_id, 0) + 1
        bot.answer_callback_query(call.id, "🗳 Ovoz berildi!")
        update_voice_buttons(bot, channel_id, konkurs)

def check_user_leave(bot, user_id, user_data):
    konkurs = user_data.get("voice")
    if not konkurs:
        return
        
    if "voted_by" in konkurs and user_id in konkurs["voted_by"]:
        voted_id = konkurs["voted_by"].pop(user_id)
        if voted_id in konkurs["votes"]:
            konkurs["votes"][voted_id] -= 1
            if konkurs["votes"][voted_id] < 0:
                konkurs["votes"][voted_id] = 0
