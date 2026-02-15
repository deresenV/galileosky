from typing import List
from src.domain.interfaces import IFileReader
from src.domain.converter import HexConverter

class HexProcessingService:
    """
    Сервис приложения для обработки hex-данных из файлов.
    """

    def __init__(self, file_reader: IFileReader):
        """
        Инициализирует сервис с зависимостью от читателя файлов.

        :param file_reader: Реализация интерфейса IFileReader.
        """
        self._file_reader = file_reader

    def process_file(self, file_path: str) -> List[int]:
        """
        Читает файл и преобразует его содержимое в массив байтов.

        :param file_path: Путь к файлу с raw-code.
        :return: Список байтов.
        """
        # Чтение содержимого файла
        raw_content = self._file_reader.read(file_path)
        
        # Конвертация через доменный сервис/утилиту
        return HexConverter.to_byte_array(raw_content)
