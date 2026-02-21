FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей
RUN pip install aiofiles prometheus-client

# Копирование исходного кода
COPY . .

# Запуск сервиса
CMD ["python", "listener_service.py"]
