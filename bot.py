import os
import logging
import requests
from aiogram import Bot, Dispatcher, types
from fastapi import FastAPI, Request
from aiogram.types import Update
from aiogram.dispatcher.webhook import Dispatcher as WebhookDispatcher

logging.basicConfig(level=logging.INFO)

# Получаем переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например, https://yourdomain.com/webhook
PORT = int(os.getenv("PORT", 8000))

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
app = FastAPI()

# --- Функция генерации текста через Replicate ---
def generate_text(prompt: str) -> str:
    """
    Отправляет запрос на replicate и возвращает сгенерированный текст
    """
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    json_data = {
        "version": "d1b68d1b966f96f97a2364cec456e84fda2d24d50eeb14abe14b509f2223ed97",  # Версия модели
        "input": {
            "prompt": prompt,
            "system_message": "Write(output) in English.",
            "max_tokens": 7000,
            "temperature": 0.7,
            "top_p": 0.9
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    prediction = response.json()
    return prediction['output'][0]  # Возвращаем первый результат

# --- Обработчики aiogram ---

@dp.message(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer("Привет! Отправь мне описание для генерации NSFW текста.")

@dp.message()
async def text_handler(message: types.Message):
    await message.answer("Генерирую текст, подожди...")

    try:
        generated_text = generate_text(message.text)
        await message.answer(generated_text)
    except Exception as e:
        await message.answer(f"Ошибка при генерации текста: {e}")

# --- FastAPI webhook endpoint ---

@app.post("/webhook")
async def webhook_handler(request: Request):
    json_update = await request.json()
    update = Update(**json_update)
    await dp.process_update(update)
    return {"ok": True}

# --- Стартап и шутдаун ---

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook установлен: {WEBHOOK_URL}")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()
    logging.info("Webhook удалён и сессия закрыта")

# --- Запуск uvicorn ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=PORT)