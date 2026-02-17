FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей
RUN pip install aiofiles

# Копирование исходного кода
COPY . .

# Запуск сервиса
CMD ["python", "listener_service.py"]
