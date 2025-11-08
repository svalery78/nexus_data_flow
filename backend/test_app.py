import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from backend.app import app

client = TestClient(app)

@pytest.fixture
def mock_db():
    """Мок для aiosqlite, который корректно работает с async with."""
    db_connection_mock = AsyncMock()
    
    # Создаем мок для контекстного менеджера
    context_manager_mock = AsyncMock()
    context_manager_mock.__aenter__.return_value = db_connection_mock
    
    # Патчим aiosqlite.connect, чтобы он возвращал наш мок-контекстный менеджер
    with patch("backend.app.aiosqlite.connect", return_value=context_manager_mock) as mock_connect:
        yield db_connection_mock

@pytest.fixture
def mock_telegram_bot():
    """Мок для telegram.Bot."""
    # Патчим метод на уровне класса, а не экземпляра
    with patch("telegram.Bot.send_message", new_callable=AsyncMock) as mock_send_message:
        yield mock_send_message

def test_submit_form_success(mock_db, mock_telegram_bot):
    """Тест успешной отправки формы."""
    response = client.post(
        "/api/submit",
        json={"name": "Test User", "email": "test@example.com", "message": "Hello"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Заявка успешно принята!"}

    # Проверяем, что были вызваны методы БД и Telegram
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_telegram_bot.assert_called_once()

def test_submit_form_db_error(mock_db, mock_telegram_bot):
    """Тест ошибки при сохранении в БД."""
    # Настраиваем мок БД, чтобы он вызывал исключение
    mock_db.execute.side_effect = Exception("Database connection failed")

    response = client.post(
        "/api/submit",
        json={"name": "Test User", "email": "test@example.com", "message": "Hello"},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": "Ошибка на сервере при работе с базой данных."}

    # Убеждаемся, что отправка в Telegram не производилась
    mock_telegram_bot.assert_not_called()

def test_submit_form_telegram_error_still_succeeds(mock_db, mock_telegram_bot):
    """Тест, проверяющий, что ошибка Telegram не проваливает весь запрос."""
    # Настраиваем мок Telegram, чтобы он вызывал исключение
    mock_telegram_bot.side_effect = Exception("Telegram API error")

    response = client.post(
        "/api/submit",
        json={"name": "Test User", "email": "test@example.com", "message": "Hello"},
    )
    # Запрос все равно должен быть успешным для пользователя
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Заявка успешно принята!"}

    # Но при этом мы должны видеть, что вызовы к БД были
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()
    # И попытка отправки в Telegram тоже была
    mock_telegram_bot.assert_called_once()

def test_submit_form_validation_error():
    """Тест ошибки валидации (отсутствует поле email)."""
    response = client.post(
        "/api/submit",
        json={"name": "Test User", "message": "Hello"}, # Отсутствует email
    )
    assert response.status_code == 422 # Unprocessable Entity
    # Проверяем, что в теле ответа есть информация об ошибке
    assert "detail" in response.json()
    assert response.json()["detail"][0]["loc"] == ["body", "email"]
    assert response.json()["detail"][0]["msg"] == "Field required"
