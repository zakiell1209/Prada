import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, Text
from dotenv import load_dotenv
import replicate

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

client = replicate.Client(api_token=REPLICATE_TOKEN)

# Настройки моделей replicate
MODEL_ID = "aitechtree/nsfw-novel-generation"

# Стили для выбора
STYLES = {
    "anime": "Anime style",
    "realistic": "Realistic style",
    "cartoon": "Cartoon style",
}

# Клавиатура выбора стиля и типа генерации
def get_main_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Аниме", callback_data="style:anime"),
         InlineKeyboardButton(text="Реализм", callback_data="style:realistic"),
         InlineKeyboardButton(text="Мультик", callback_data="style:cartoon")],
        [InlineKeyboardButton(text="Сгенерировать картинку", callback_data="generate:image"),
         InlineKeyboardButton(text="Сгенерировать видео", callback_data="generate:video")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Состояние хранения выбора пользователя (очень простой вариант)
users_state = {}

def text_to_prompt(text: str, style_key: str):
    # Простой шаблон конвертации текста и стиля в промт для модели
    style_description = STYLES.get(style_key, "")
    prompt = f"{text}. Style: {style_description}. NSFW explicit content."
    return prompt

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    users_state[message.from_user.id] = {"style": "anime", "type": "image"}
    await message.answer(
        "Привет! Я бот для генерации NSFW изображений и видео.\n"
        "Выбери стиль и тип генерации, а потом отправь описание для промта.",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(Text(startswith="style:"))
async def style_chosen(call: types.CallbackQuery):
    style_key = call.data.split(":")[1]
    users_state.setdefault(call.from_user.id, {})["style"] = style_key
    await call.answer(f"Выбран стиль: {STYLES[style_key]}")
    await call.message.edit_reply_markup(reply_markup=get_main_keyboard())

@dp.callback_query(Text(startswith="generate:"))
async def generate_type_chosen(call: types.CallbackQuery):
    gen_type = call.data.split(":")[1]
    users_state.setdefault(call.from_user.id, {})["type"] = gen_type
    await call.answer(f"Выбран тип генерации: {'Видео' if gen_type == 'video' else 'Изображение'}")
    await call.message.edit_reply_markup(reply_markup=get_main_keyboard())

@dp.message()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    state = users_state.get(user_id, {"style": "anime", "type": "image"})
    style = state["style"]
    gen_type = state["type"]

    prompt = text_to_prompt(message.text, style)

    await message.answer(f"Генерирую {gen_type} в стиле {STYLES[style]}...\nПромт: {prompt}")

    try:
        if gen_type == "image":
            output_url = await generate_image(prompt)
            await message.answer_photo(photo=output_url)
        else:
            output_url = await generate_video(prompt)
            await message.answer(f"Видео готово: {output_url}")
    except Exception as e:
        await message.answer(f"Ошибка генерации: {e}")

async def generate_image(prompt: str) -> str:
    # Вызываем модель replicate для изображения
    model = client.models.get(MODEL_ID)
    version = model.versions.list()[0]  # Берем последнюю версию модели

    output = version.predict(prompt=prompt)
    # output — ссылка на сгенерированное изображение
    if isinstance(output, list):
        return output[0]
    return output

async def generate_video(prompt: str) -> str:
    # Заглушка, пока видеогенерация не реализована в модели
    # Можно добавить вызов другой модели replicate, если нужна
    # Временно возвращаем сообщение
    return "Видео генерация пока не поддерживается в этой модели."

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())