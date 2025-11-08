import uvicorn
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import psycopg2
import telegram
import os
from dotenv import load_dotenv
import logging

# --- Конфигурация ---
load_dotenv()

# --- Логирование ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Модели данных ---
class ApplicationData(BaseModel):
    name: str
    email: str
    message: str

# --- Инициализация ---
app = FastAPI()

# --- Эндпоинты ---
@app.post("/api/submit")
async def submit_form(data: ApplicationData):
    """
    Принимает данные из формы, сохраняет в БД и отправляет уведомление в Telegram.
    """
    logging.info(f"Получены данные: {data.dict()}")
    
    # Здесь будет логика сохранения в БД и отправки уведомления
    
    return {"status": "ok", "message": "Заявка успешно принята!"}

# --- Запуск приложения ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
