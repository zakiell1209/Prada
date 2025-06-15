import os
import replicate
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

# 🔐 Вставьте сюда токены
REPLICATE_TOKEN = "репликейт_токен"
TELEGRAM_TOKEN = "тг_токен"

os.environ["REPLICATE_API_TOKEN"] = REPLICATE_TOKEN

bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# 🎨 Кнопки выбора стиля
style_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎎 Аниме"), KeyboardButton(text="🎨 Реализм")],
        [KeyboardButton(text="🧠 Промт вручную")]
    ],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("👋 Привет! Выбери стиль генерации изображения:", reply_markup=style_kb)

# 📩 Обработка выбора
@dp.message()
async def handle_message(message: Message):
    text = message.text.lower()

    if "аниме" in text:
        await message.answer("✍️ Введи описание изображения (аниме):")
        dp.message.register(generate_image, style="anime")
    elif "реализм" in text:
        await message.answer("✍️ Введи описание изображения (реализм):")
        dp.message.register(generate_image, style="realism")
    elif "промт" in text:
        await message.answer("✍️ Введи промт напрямую:")
        dp.message.register(generate_prompt)
    else:
        await message.answer("😕 Пожалуйста, выбери стиль с помощью кнопок.")

# 🧠 Промт напрямую
async def generate_prompt(message: Message):
    await message.answer("🔄 Генерирую...")
    output = replicate.run(
        "aitechtree/nsfw-novel-generation",
        input={"prompt": message.text}
    )
    await message.reply_photo(output[0])

# 🤖 Автогенерация промта
async def generate_image(message: Message, style: str):
    prompt = f"{style}, {message.text}"
    await message.answer("🎨 Генерирую...")
    output = replicate.run(
        "aitechtree/nsfw-novel-generation",
        input={"prompt": prompt}
    )
    await message.reply_photo(output[0])

# ▶️ Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())