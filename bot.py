import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import replicate

# Токен телеги и replicate токен — вставь свои
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Инициализация клиента replicate
client = replicate.Client(api_token=REPLICATE_API_TOKEN)

# Стили для генерации
STYLES = {
    "anime": "anime style, colorful, detailed",
    "realistic": "realistic photo, high resolution, 4k",
    "nsfw": "nsfw, explicit, detailed",
    "cyberpunk": "cyberpunk style, neon lights",
}

# Кнопки выбора стиля и видео
style_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Аниме", callback_data="style:anime"),
     InlineKeyboardButton(text="Реализм", callback_data="style:realistic")],
    [InlineKeyboardButton(text="NSFW", callback_data="style:nsfw"),
     InlineKeyboardButton(text="Киберпанк", callback_data="style:cyberpunk")],
    [InlineKeyboardButton(text="Создать Видео", callback_data="video:start")],
])

# Состояния пользователя (стиль, режим)
users_settings = {}

# Функция конвертации пользовательского ввода в промт
def create_prompt(text: str, style: str) -> str:
    base_prompt = f"{text.strip()}, {STYLES.get(style, '')}"
    return base_prompt

# Хендлер старт
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    users_settings[message.from_user.id] = {"style": "realistic", "video": False}
    await message.answer(
        "Привет! Я бот для генерации изображений и видео с поддержкой NSFW.\n"
        "Выбери стиль и отправь описание для генерации.\n",
        reply_markup=style_kb
    )

# Хендлер кнопок
@dp.callback_query(Text(startswith="style:"))
async def style_chosen(call: types.CallbackQuery):
    style = call.data.split(":")[1]
    users_settings[call.from_user.id] = users_settings.get(call.from_user.id, {"style":"realistic", "video": False})
    users_settings[call.from_user.id]["style"] = style
    users_settings[call.from_user.id]["video"] = False
    await call.answer(f"Стиль выбран: {style}")
    await call.message.answer("Отправь описание (на русском) для генерации изображения:")

@dp.callback_query(Text(startswith="video:"))
async def video_chosen(call: types.CallbackQuery):
    users_settings[call.from_user.id] = users_settings.get(call.from_user.id, {"style":"realistic", "video": False})
    users_settings[call.from_user.id]["video"] = True
    await call.answer("Режим видео выбран")
    await call.message.answer("Отправь описание (на русском) для генерации видео:")

# Хендлер текста — генерация
@dp.message(F.text)
async def generate_handler(message: types.Message):
    user_id = message.from_user.id
    settings = users_settings.get(user_id, {"style": "realistic", "video": False})
    prompt = create_prompt(message.text, settings["style"])

    await message.answer(f"Генерирую {'видео' if settings['video'] else 'изображение'}...\nПромт:\n{prompt}")

    try:
        if settings["video"]:
            # Запуск генерации видео через replicate (пример модели)
            # Замените на актуальную модель генерации видео с replicate
            model = client.models.get("aitechtree/nsfw-novel-generation")  # можно поменять
            version = model.versions.list()[0]  # берем последнюю версию
            prediction = client.predictions.create(
                version=version.id,
                input={"prompt": prompt, "mode": "video"}
            )
            # Ждем пока закончится (упрощенно)
            while prediction.status not in ["succeeded", "failed", "canceled"]:
                await asyncio.sleep(3)
                prediction = client.predictions.get(id=prediction.id)
            if prediction.status == "succeeded":
                await message.answer(f"Видео готово:\n{prediction.output}")
            else:
                await message.answer(f"Ошибка генерации видео: {prediction.status}")
        else:
            # Генерация изображения
            model = client.models.get("aitechtree/nsfw-novel-generation")
            version = model.versions.list()[0]
            prediction = client.predictions.create(
                version=version.id,
                input={"prompt": prompt}
            )
            # Ждем окончания
            while prediction.status not in ["succeeded", "failed", "canceled"]:
                await asyncio.sleep(2)
                prediction = client.predictions.get(id=prediction.id)
            if prediction.status == "succeeded":
                # prediction.output — ссылка на изображение или список ссылок
                output = prediction.output
                if isinstance(output, list):
                    output = output[0]
                await message.answer_photo(photo=output)
            else:
                await message.answer(f"Ошибка генерации изображения: {prediction.status}")

    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")

    await message.answer("Выбери стиль или видео для новой генерации:", reply_markup=style_kb)

# Запуск бота
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)