from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

BOT_TOKEN = "8452391283:AAESGiQ0GClTdX8aElJonmj3194lpNin00M"
ADMIN_ID = 7617397626
BOT_USERNAME = "@unversal_konkurs_bot"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📊 Statistika", callback_data="stats"),
            InlineKeyboardButton("📢 Reklama yuborish", callback_data="ads")
        )
        await message.answer(
            "👋 Salom, admin!\nQuyidagi panel orqali botni boshqaring:",
            reply_markup=markup
        )
    else:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📖 Qoidalarni o‘qish", callback_data="rules"),
            InlineKeyboardButton("📢 Kanalga qo‘shilish", url="https://t.me/yourchannel")
        )
        await message.answer(
            f"🎉 Salom, {message.from_user.first_name}!\nBu bot orqali turli *konkurslarda* ishtirok etishingiz mumkin!",
            parse_mode="Markdown",
            reply_markup=markup
        )

@dp.callback_query_handler(lambda c: c.data in ["stats", "ads", "rules"])
async def callback_handler(callback_query: types.CallbackQuery):
    data = callback_query.data

    if data == "stats":
        await callback_query.message.answer("📊 Statistikalar hali tayyor emas.")
    elif data == "ads":
        await callback_query.message.answer("📢 Reklama yuborish funksiyasi tez orada yoqiladi.")
    elif data == "rules":
        await callback_query.message.answer(
            "📘 *Qoidalar:*\n1. Kanalga a’zo bo‘ling.\n2. Konkursda adolat bilan ishtirok eting.\n3. Spam va so‘kinish taqiqlanadi.",
            parse_mode="Markdown"
        )

async def main():
    print("🤖 Bot ishga tushdi...")
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
