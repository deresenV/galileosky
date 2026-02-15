from abc import ABC, abstractmethod
from typing import Dict, Any

class IStorage(ABC):
    """
    Интерфейс для сохранения распарсенных данных.
    """
    
    @abstractmethod
    async def save(self, packet_data: Dict[str, Any]):
        """
        Сохраняет данные пакета.
        :param packet_data: Словарь с данными пакета.
        """
        pass
