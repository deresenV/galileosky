from typing import List, Tuple, Optional
from src.domain.tags import Tags, Tag
from src.domain.models import ParsedTag, ParsedPacket

class TagParser:
    """
    Парсер для последовательного чтения тегов из байтового массива.
    """

    def parse(self, data: List[int]) -> ParsedPacket:
        """
        Парсит массив байтов, извлекая теги.
        
        :param data: Список байтов.
        :return: ParsedPacket, содержащий найденные теги и пропущенные байты.
        """
        index = 0
        parsed_tags = []
        skipped_bytes = []
        
        while index < len(data):
            byte = data[index]
            tag = Tags.get_tag(byte)
            
            if tag:
                try:
                    # Попытка распарсить тег
                    parsed_tag, new_index = self._process_tag(tag, data, index)
                    parsed_tags.append(parsed_tag)
                    index = new_index
                except (IndexError, ValueError):
                    # Если данных не хватает или структура некорректна
                    # Добавляем текущий байт в пропущенные и пробуем следующий
                    skipped_bytes.append(byte)
                    index += 1
            else:
                # Байт не является известным тегом
                skipped_bytes.append(byte)
                index += 1
                
        return ParsedPacket(tags=parsed_tags, skipped_bytes=skipped_bytes)

    def _process_tag(self, tag: Tag, data: List[int], start_index: int) -> Tuple[ParsedTag, int]:
        """
        Обрабатывает один тег, определяя его длину и данные.
        
        :param tag: Объект Tag.
        :param data: Исходные данные.
        :param start_index: Индекс начала тега (где находится сам байт тега).
        :return: Кортеж (ParsedTag, новый индекс после данных тега).
        :raises IndexError: Если данных недостаточно.
        """
        current_index = start_index + 1 # Пропускаем сам байт тега
        
        data_length = 0
        
        if tag.num == 0xEA:
            # Длина указана в следующем байте (1 байт длины)
            if current_index >= len(data):
                raise IndexError("Unexpected end of data for tag 0xEA length")
            
            data_length = data[current_index]
            current_index += 1 # Пропускаем байт длины
            
        elif tag.num == 0xFE:
            # Расширенные теги. По описанию: "длина данных указана в следующих байтах".
            # Обычно это 2 байта длины (Little Endian).
            if current_index + 1 >= len(data):
                raise IndexError("Unexpected end of data for tag 0xFE length")
            
            # Читаем 2 байта длины (Little Endian)
            l_low = data[current_index]
            l_high = data[current_index + 1]
            data_length = l_low + (l_high << 8)
            
            current_index += 2 # Пропускаем 2 байта длины
            
        else:
            # Обычный тег с фиксированной длиной
            data_length = tag.length

        # Проверка, хватает ли данных
        if current_index + data_length > len(data):
             raise IndexError(f"Not enough data for tag {tag.tag_hex_str}. Expected {data_length}, got {len(data) - current_index}")

        tag_data = data[current_index : current_index + data_length]
        
        return ParsedTag(tag=tag, data=tag_data), current_index + data_length
