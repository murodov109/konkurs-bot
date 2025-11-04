import random

def random_konkurs(bot, call):
    bot.send_message(call.message.chat.id, "🎲 Random konkurs boshlandi!")
    participants = ["Ali", "Vali", "Gulbahor", "Dilshod", "Javohir"]
    winner = random.choice(participants)
    bot.send_message(
        call.message.chat.id,
        f"🎉 Tasodifiy g‘olib: {winner}!\nTabriklaymiz!\n"
        "Bot: @unversal_konkurs_bot"
    )
