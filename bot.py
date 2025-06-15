import os
import replicate
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.utils.markdown import hbold
from fastapi import FastAPI, Request
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import setup_application
import uvicorn

# 🔧 Конфигурация
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_MODEL = "aitechtree/nsfw-novel-generation"

bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()

replicate_client = replicate.Client(api_token=REPLICATE_TOKEN)

# 📥 Обработка команд
@dp.message(CommandStart())
async def start(msg: Message):
    await msg.answer("👋 Привет! Отправь описание сцены, и я сгенерирую NSFW изображение.")

@dp.message()
async def generate_image(msg: Message):
    prompt = msg.text.strip()
    await msg.answer("🎨 Генерация изображения, подожди...")

    try:
        output = replicate_client.run(
            REPLICATE_MODEL,
            input={"prompt": prompt}
        )
        if isinstance(output, list):
            await msg.answer_photo(output[0])
        else:
            await msg.answer("❌ Не удалось получить изображение.")
    except Exception as e:
        await msg.answer(f"⚠️ Ошибка: {str(e)}")

# 🌐 Вебхук роут
@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    await dp.feed_webhook_update(bot, body)
    return {"ok": True}

# 🧩 Настройка FastAPI + aiogram
def main():
    import asyncio
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    dp.startup.register(lambda _: bot.set_webhook("https://YOUR-RENDER-URL.onrender.com/webhook"))

    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()