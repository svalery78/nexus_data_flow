import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aiosqlite # Изменено с psycopg2
import telegram
import os
from dotenv import load_dotenv
import logging
from fastapi.middleware.cors import CORSMiddleware # Добавлено

# --- Конфигурация ---
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Логирование ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Модели данных ---
class ApplicationData(BaseModel):
    name: str
    email: str
    message: str

# --- Инициализация ---
app = FastAPI()
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# Добавление CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники для разработки
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все HTTP методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

# --- Эндпоинты ---
@app.post("/api/submit")
async def submit_form(data: ApplicationData):
    """
    Принимает данные из формы, сохраняет в БД и отправляет уведомление в Telegram.
    """
    logging.info(f"Получены данные: {data.model_dump()}")

    # 1. Сохранение в базу данных SQLite
    db_path = DATABASE_URL.replace("sqlite:///./", "") # Извлечение пути к файлу БД
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "INSERT INTO applications (name, email, message) VALUES (?, ?, ?)", # ? для SQLite
                (data.name, data.email, data.message)
            )
            await db.commit()
        logging.info("Данные успешно сохранены в БД SQLite.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении в БД SQLite: {e}")
        raise HTTPException(status_code=500, detail="Ошибка на сервере при работе с базой данных.")

    # 2. Отправка уведомления в Telegram
    try:
        # Используем HTML для большей надежности
        message_text = (
            f"🎉 <b>Новая заявка!</b>\n\n"
            f"👤 <b>Имя:</b> {data.name}\n"
            f"📧 <b>Email:</b> {data.email}\n"
            f"📝 <b>Сообщение:</b>\n{data.message}"
        )
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message_text,
            parse_mode='HTML' # Изменено на HTML
        )
        logging.info("Уведомление в Telegram успешно отправлено.")
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления в Telegram: {e}")
        # Не возвращаем ошибку пользователю, т.к. заявка уже сохранена
        # Но логируем проблему.

    return {"status": "ok", "message": "Заявка успешно принята!"}

# --- Запуск приложения ---
if __name__ == "__main__":
    if not all([DATABASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        logging.error("Не все переменные окружения заданы! Проверьте .env файл.")
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)
