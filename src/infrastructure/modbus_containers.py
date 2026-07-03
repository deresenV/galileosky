import json
import logging
import os
from typing import Dict

from src.config import config

logger = logging.getLogger(__name__)


class ModbusContainerRegistry:
    """
    Реестр соответствия Modbus-порт -> container_id.

    Хранится в JSON в корне проекта в виде {"modbus0": 1, "modbus1": 2, ...}.
    Файл создаётся автоматически (под все Modbus-порты) при первом запуске и
    перечитывается на лету при его изменении — это позволяет менять привязку
    контейнеров без перезапуска сервиса.
    """

    def __init__(self, path: str, ports: int):
        self.path = path
        self.ports = ports
        self._mtime = None
        self._mapping: Dict[str, str] = {}
        self._ensure_file()
        self._reload()

    def _default_mapping(self) -> Dict[str, int]:
        """Значение по умолчанию: номер порта (потом правится вручную)."""
        return {f"modbus{i}": i for i in range(self.ports)}

    def _ensure_file(self) -> None:
        if os.path.exists(self.path):
            return
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._default_mapping(), f, ensure_ascii=False, indent=2)
            logger.info(f"Created modbus containers file: {self.path}")
        except Exception as e:
            logger.error(f"Failed to create modbus containers file {self.path}: {e}")

    def _reload(self) -> None:
        """Перечитать файл, если он изменился (по mtime)."""
        try:
            mtime = os.path.getmtime(self.path)
        except OSError:
            return
        if mtime == self._mtime:
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._mapping = {str(k): str(v) for k, v in data.items()}
            self._mtime = mtime
            logger.info(f"Reloaded modbus containers mapping from {self.path}")
        except Exception as e:
            # Файл могли править в момент чтения — оставляем прошлую карту
            logger.warning(f"Failed to read modbus containers file {self.path}: {e}")

    def get_container_id(self, modbus_key: str) -> str:
        """container_id для Modbus-порта (например 'modbus0'); 'unknown' если нет."""
        self._reload()
        return self._mapping.get(modbus_key, "unknown")


modbus_containers = ModbusContainerRegistry(config.MODBUS_CONTAINERS_FILE, config.MODBUS_PORTS)
