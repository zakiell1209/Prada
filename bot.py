import os
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from pydantic import BaseModel
from aiogram.utils import executor

# Ваш токен бота
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Репликационный API и ключ
REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY")
REPLICATE_MODEL = "aitechtree/nsfw-novel-generation"

# Создание бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Шаблоны для генерации изображений
TEMPLATES = {
    "аниме": "A cute anime girl with a magical background.",
    "реализм": "A realistic painting of a beautiful landscape.",
}

# Структура для запроса на генерацию
class ImageRequest(BaseModel):
    prompt: str
    style: str
    is_video: bool = False


# Функция для отправки запроса в Replicate
def generate_image_from_replica(prompt: str, style: str, is_video: bool = False):
    headers = {
        "Authorization": f"Bearer {REPLICATE_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "version": "v1",
        "input": {
            "prompt": prompt,
            "style": style,
            "is_video": is_video
        }
    }

    response = requests.post(f"https://api.replicate.com/v1/predictions", json=payload, headers=headers)
    result = response.json()
    
    return result['urls']['image'] if not is_video else result['urls']['video']


# Кнопки выбора стиля
async def generate_style_buttons():
    keyboard = InlineKeyboardMarkup(row_width=2)
    button_anime = InlineKeyboardButton("Аниме", callback_data="anime")
    button_realism = InlineKeyboardButton("Реализм", callback_data="realism")
    keyboard.add(button_anime, button_realism)
    return keyboard


# Кнопка для генерации видео
async def generate_video_button():
    keyboard = InlineKeyboardMarkup(row_width=1)
    button_video = InlineKeyboardButton("Создать видео", callback_data="video")
    keyboard.add(button_video)
    return keyboard


# Обработчик команды старт
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    welcome_text = "Привет! Я бот для генерации изображений. Выберите стиль:"
    keyboard = await generate_style_buttons()
    await message.answer(welcome_text, reply_markup=keyboard)


# Обработчик выбора стиля
@dp.callback_query_handler(lambda c: c.data in ['anime', 'realism'])
async def process_style(callback_query: types.CallbackQuery):
    style = callback_query.data
    prompt = TEMPLATES[style]  # Используем шаблон для выбранного стиля
    is_video = False  # Пока не создаём видео
    image_url = generate_image_from_replica(prompt, style, is_video)
    
    await bot.send_photo(callback_query.from_user.id, image_url)
    await callback_query.answer()


# Обработчик кнопки для генерации видео
@dp.callback_query_handler(lambda c: c.data == 'video')
async def process_video(callback_query: types.CallbackQuery):
    prompt = "A futuristic cityscape at night."  # Пример текста для видео
    style = "реализм"
    is_video = True
    video_url = generate_image_from_replica(prompt, style, is_video)
    
    await bot.send_video(callback_query.from_user.id, video_url)
    await callback_query.answer()


# Обработчик ввода текста для генерации
@dp.message_handler(content_types=types.ContentType.TEXT)
async def generate_from_text(message: types.Message):
    user_input = message.text
    prompt = f"Generate an image of {user_input}"  # Конвертация текста в промт
    style = "аниме"  # Выбираем стиль по умолчанию
    is_video = False
    image_url = generate_image_from_replica(prompt, style, is_video)
    
    await message.answer(f"Вот изображение по вашему запросу: {user_input}")
    await bot.send_photo(message.from_user.id, image_url)


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)