# Базовый образ с Python 3.9
FROM python:3.10-slim

# Установим рабочую директорию внутри контейнера
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение
COPY . .

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

RUN pip install passlib[bcrypt]
