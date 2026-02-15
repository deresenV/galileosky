import os
from src.domain.interfaces import IFileReader

class LocalFileReader(IFileReader):
    """
    Реализация чтения локальных файлов.
    """

    def read(self, path: str) -> str:
        """
        Читает содержимое файла с диска.

        :param path: Абсолютный или относительный путь к файлу.
        :return: Содержимое файла.
        :raises FileNotFoundError: Если файл не найден.
        :raises IOError: При ошибках чтения.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Файл не найден по пути: {path}")

        try:
            with open(path, 'r', encoding='utf-8') as file:
                return file.read()
        except IOError as e:
            raise IOError(f"Ошибка при чтении файла {path}: {e}")
