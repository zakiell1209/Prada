import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import httpx

# ========== Настройки ==========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Токен твоего телеграм-бота
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")  # Токен replicate

if not TELEGRAM_TOKEN or not REPLICATE_API_TOKEN:
    print("Ошибка! Задай TELEGRAM_TOKEN и REPLICATE_API_TOKEN в переменных окружения.")
    exit(1)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ================== Кнопки выбора стиля и типа ===================
STYLE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Аниме", callback_data="style:anime"),
        InlineKeyboardButton(text="Реализм", callback_data="style:realism"),
    ],
    [
        InlineKeyboardButton(text="Сгенерировать Видео", callback_data="type:video"),
        InlineKeyboardButton(text="Сгенерировать Картинку", callback_data="type:image"),
    ],
])

# Хранение состояния для каждого пользователя (можно заменить на БД для продакшена)
user_settings = {}

# ============ Функции конвертации текста в промты для каждого стиля =============
def convert_to_prompt(text: str, style: str) -> str:
    base_prompt = text.strip()
    if style == "anime":
        # простой шаблон для аниме стиля
        return f"anime style, detailed, {base_prompt}"
    elif style == "realism":
        return f"realistic, photo quality, {base_prompt}"
    else:
        return base_prompt

# =============== Вызов replicate API для генерации изображения или видео ===============
async def replicate_generate(prompt: str, is_video: bool = False) -> str:
    # Используем модель aitechtree/nsfw-novel-generation для примера
    model_version = "aitechtree/nsfw-novel-generation:1d2c8f0f8f05ca5fbc4710e5d2701d7ee5553c70c917fd11db9d93bf6f3124f5"
    api_url = f"https://api.replicate.com/v1/predictions"

    input_data = {
        "prompt": prompt,
        "mode": "video" if is_video else "image",
    }

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(
            api_url,
            headers=headers,
            json={
                "version": model_version,
                "input": input_data,
            },
        )
        response.raise_for_status()
        prediction = response.json()

    # Ждём, пока предсказание завершится
    prediction_url = f"https://api.replicate.com/v1/predictions/{prediction['id']}"
    while True:
        async with httpx.AsyncClient(timeout=300) as client:
            status_resp = await client.get(prediction_url, headers=headers)
            status_resp.raise_for_status()
            status_data = status_resp.json()

        status = status_data["status"]
        if status == "succeeded":
            output = status_data["output"]
            if isinstance(output, list):
                # если несколько ссылок - берём первую
                return output[0]
            return output
        elif status == "failed":
            raise Exception("Ошибка генерации в replicate: " + str(status_data))
        await asyncio.sleep(2)

# ======================= Обработчики Telegram =======================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_settings[message.from_user.id] = {"style": "anime", "type": "image"}
    await message.answer(
        "Привет! Я бот для генерации NSFW изображений и видео.\n"
        "Выбери стиль и тип генерации с помощью кнопок ниже.\n"
        "Отправь мне описание для генерации.",
        reply_markup=STYLE_KEYBOARD,
    )

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    if data.startswith("style:"):
        style = data.split(":")[1]
        user_settings.setdefault(user_id, {})["style"] = style
        await callback.answer(f"Выбран стиль: {style}")
    elif data.startswith("type:"):
        gen_type = data.split(":")[1]
        user_settings.setdefault(user_id, {})["type"] = gen_type
        await callback.answer(f"Выбран тип генерации: {gen_type}")

@dp.message()
async def generate_handler(message: types.Message):
    user_id = message.from_user.id
    settings = user_settings.get(user_id, {"style": "anime", "type": "image"})

    style = settings["style"]
    gen_type = settings["type"]

    prompt = convert_to_prompt(message.text, style)

    await message.answer("Генерирую, пожалуйста подожди...")

    try:
        is_video = gen_type == "video"
        output_url = await replicate_generate(prompt, is_video)
        if is_video:
            await message.answer_video(output_url)
        else:
            await message.answer_photo(output_url)
    except Exception as e:
        await message.answer(f"Ошибка генерации: {e}")

# ======================== Запуск бота ========================
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    print("Бот запущен...")

    import asyncio

    asyncio.run(dp.start_polling(bot))