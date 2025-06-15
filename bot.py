import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import replicate

# Токены
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Токен телеги
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")  # Токен replicate

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

client = replicate.Client(api_token=REPLICATE_API_TOKEN)

# Пример модели NSFW с replicate (замени на нужную тебе модель)
MODEL_NAME = "aitechtree/nsfw-novel-generation"  # или другая nsfw-модель
MODEL_VERSION = None  # если хочешь, укажи версию

@dp.message(Command(commands=["start", "help"]))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Отправь описание, и я сгенерирую NSFW изображение через replicate.\n"
        "Пример: красивая девушка в аниме стиле\n"
        "Без ограничений, без цензуры."
    )

@dp.message()
async def generate_image(message: Message):
    prompt = message.text.strip()
    if not prompt:
        await message.answer("Пожалуйста, отправь описание для генерации.")
        return

    await message.answer("Генерирую изображение, подожди...")

    try:
        # Генерация через replicate
        model = client.models.get(MODEL_NAME)
        version = MODEL_VERSION or model.versions.list()[0]  # берем последнюю, если не указанна

        output = version.predict(prompt=prompt)
        # output может быть списком URL или одним URL — в зависимости от модели
        if isinstance(output, list):
            image_url = output[0]
        else:
            image_url = output

        await message.answer_photo(photo=image_url, caption=f"Результат для:\n{prompt}")

    except Exception as e:
        await message.answer(f"Произошла ошибка при генерации: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())