document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#nexus-form");
    const responseMessageContainer = document.querySelector("#nexus-response-message");

    if (!form) {
        console.error("Форма с ID #nexus-form не найдена.");
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault(); // Предотвращаем стандартную отправку формы

        // Очищаем предыдущие сообщения
        if(responseMessageContainer) responseMessageContainer.innerHTML = '';

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // Простая валидация на стороне клиента
        if (!data.name || !data.email || !data.message) {
            displayMessage("Пожалуйста, заполните все обязательные поля.", "error");
            return;
        }

        try {
            const response = await fetch("http://127.0.0.1:8000/api/submit", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();

            if (response.ok) {
                displayMessage("Ваша заявка успешно отправлена!", "success");
                form.reset(); // Очищаем форму
            } else {
                // Показываем ошибку от сервера
                const errorMessage = result.detail || "Произошла неизвестная ошибка.";
                displayMessage(`Ошибка: ${errorMessage}`, "error");
            }
        } catch (error) {
            console.error("Ошибка при отправке запроса:", error);
            displayMessage("Не удалось подключиться к серверу. Попробуйте позже.", "error");
        }
    });

    function displayMessage(message, type) {
        if (!responseMessageContainer) {
            // Если контейнер для сообщений не найден, используем alert
            alert(message);
            return;
        }
        responseMessageContainer.className = `nexus-message--${type}`;
        responseMessageContainer.textContent = message;
    }
});
