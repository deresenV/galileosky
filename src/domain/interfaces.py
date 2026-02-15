from abc import ABC, abstractmethod

class IFileReader(ABC):
    """
    Интерфейс для чтения файлов.
    """

    @abstractmethod
    def read(self, path: str) -> str:
        """
        Читает содержимое файла.

        :param path: Путь к файлу.
        :return: Содержимое файла в виде строки.
        """
        pass
