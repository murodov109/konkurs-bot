BOT_TOKEN = "8452391283:AAESGiQ0GClTdX8aElJonmj3194lpNin00M"
from telebot import TeleBot, types
from voice import voice_konkurs, handle_voice_callbacks
from link import link_konkurs, add_invite, show_invite_stats
from battle import battle_konkurs
from random_konkurs import random_konkurs

BOT_TOKEN = "8452391283:AAESGiQ0GClTdX8aElJonmj3194lpNin00M"
ADMIN_ID = 7617397626
BOT_USERNAME = "@unversal_konkurs_bot"

bot = TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    # agar taklif havolasi bilan kirgan bo‘lsa
    parts = message.text.split()
    if len(parts) == 2 and parts[1].isdigit():
        inviter_id = int(parts[1])
        add_invite(bot, message, inviter_id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🎤 Ovozniy konkurs", callback_data="voice")
    btn2 = types.InlineKeyboardButton("🔗 Taklif havolali konkurs", callback_data="link")
    btn3 = types.InlineKeyboardButton("⚔️ Batl konkursi", callback_data="battle")
    btn4 = types.InlineKeyboardButton("🎲 Random konkurs", callback_data="random")
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(
        message.chat.id,
        "📋 Konkurs turini tanlang:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "voice":
        voice_konkurs(bot, call)
    elif call.data == "link":
        link_konkurs(bot, call)
    elif call.data == "battle":
        battle_konkurs(bot, call)
    elif call.data == "random":
        random_konkurs(bot, call)
    elif call.data.startswith("join_voice") or call.data.startswith("vote_voice"):
        handle_voice_callbacks(bot, call)
    elif call.data == "show_invites":
        show_invite_stats(bot, call)

bot.polling(none_stop=True)
