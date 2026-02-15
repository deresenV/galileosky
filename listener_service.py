import asyncio
import logging
import sys
from src.infrastructure.listener_adapter import GalileoskyListenerAdapter
from src.config import config

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
    adapter = GalileoskyListenerAdapter(config.HOST, config.PORT)
    await adapter.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
