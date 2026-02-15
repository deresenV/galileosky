from typing import List

class HexConverter:
    """
    Класс для конвертации шестнадцатеричных строк.
    """

    @staticmethod
    def to_byte_array(hex_string: str) -> List[int]:
        """
        Преобразует шестнадцатеричную строку в массив байтов.

        :param hex_string: Строка, содержащая hex-данные.
        :return: Список целых чисел (байтов).
        :raises ValueError: Если строка содержит некорректные символы.
        """
        clean_hex = hex_string.strip().replace(" ", "").replace("\n", "")
        try:
            return list(bytes.fromhex(clean_hex))
        except ValueError as e:
            # Обработка ошибки некорректного формата
            raise ValueError(f"Некорректный формат hex-строки: {e}")
