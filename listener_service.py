import asyncio
import logging
import sys
from src.infrastructure.listener_adapter import GalileoskyListenerAdapter
from src.config import config
from prometheus_client import start_http_server

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def main():
    """
    Точка входа для запуска сервиса слушателя.
    """
    # Запуск сервера метрик Prometheus
    try:
        start_http_server(8000)
        logging.info("Prometheus metrics server started on port 8000")
    except Exception as e:
        logging.error(f"Failed to start Prometheus metrics server: {e}")

    adapter = GalileoskyListenerAdapter(config.HOST, config.PORT)
    await adapter.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
