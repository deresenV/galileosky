import struct
from typing import List, Any, Dict, Union
from src.domain.mercury import Mercury230Decoder

class TagDecoder:
    """
    Сервис для декодирования сырых байтов тегов в человекочитаемые значения.
    """

    @staticmethod
    def decode(tag_num: int, data: List[int]) -> Any:
        """
        Декодирует данные тега на основе его номера.
        """
        if not data:
            return None

        byte_data = bytes(data)

        try:
            if tag_num == 0x10:  # Номер записи
                return TagDecoder._decode_uint16(byte_data)
            elif tag_num == 0x20:  # Дата и время (Unix time)
                return TagDecoder._decode_uint32(byte_data)
            elif tag_num == 0x21:  # Миллисекунды
                return TagDecoder._decode_uint16(byte_data)
            elif tag_num == 0x30:  # Координаты
                return TagDecoder._decode_coordinates(byte_data)
            elif tag_num == 0x33:  # Скорость и направление
                return TagDecoder._decode_speed_direction(byte_data)
            elif tag_num == 0x34:  # Высота
                return TagDecoder._decode_int16(byte_data)
            elif tag_num == 0x35:  # HDOP
                return TagDecoder._decode_uint8(byte_data)
            elif tag_num == 0x40:  # Статус устройства
                return TagDecoder._decode_uint16(byte_data)
            elif tag_num in (0x41, 0x42):  # Напряжение питания/АКБ
                return TagDecoder._decode_uint16(byte_data)
            elif tag_num == 0x43:  # Температура
                return TagDecoder._decode_int8(byte_data)
            elif tag_num == 0x48:  # Расширенный статус
                return TagDecoder._decode_uint16(byte_data)
            elif tag_num == 0x49:  # Канал передачи
                return TagDecoder._decode_uint8(byte_data)
            elif tag_num in range(0x50, 0x56):  # Входы 0-5
                return TagDecoder._decode_uint16(byte_data)
            elif tag_num == 0xD4:  # Пробег
                return TagDecoder._decode_uint32(byte_data)
            elif tag_num == 0xEA: # Массив пользователя (Меркурий 230?)
                 # Пытаемся декодировать как Меркурий
                 mercury_data = Mercury230Decoder.decode(data)
                 if mercury_data:
                     return mercury_data
                 return f"Raw: {byte_data.hex().upper()}"
            elif tag_num == 0xFE: # Расширенные теги
                 return f"Raw: {byte_data.hex().upper()}"
            else:
                return byte_data.hex().upper()
        except struct.error:
             return f"Error decoding: {byte_data.hex()}"

    @staticmethod
    def _decode_uint8(data: bytes) -> int:
        return struct.unpack('<B', data)[0]

    @staticmethod
    def _decode_int8(data: bytes) -> int:
        return struct.unpack('<b', data)[0]

    @staticmethod
    def _decode_uint16(data: bytes) -> int:
        return struct.unpack('<H', data)[0]

    @staticmethod
    def _decode_int16(data: bytes) -> int:
        return struct.unpack('<h', data)[0]

    @staticmethod
    def _decode_uint32(data: bytes) -> int:
        return struct.unpack('<I', data)[0]

    @staticmethod
    def _decode_int32(data: bytes) -> int:
        return struct.unpack('<i', data)[0]

    @staticmethod
    def _decode_coordinates(data: bytes) -> Dict[str, Union[float, int]]:
        if len(data) != 9:
            return {"error": "Invalid length for coords"}
            
        lat_raw = struct.unpack('<i', data[0:4])[0]
        lon_raw = struct.unpack('<i', data[4:8])[0]
        status_byte = data[8]
        
        satellites = status_byte & 0x0F
        
        return {
            "latitude": lat_raw / 1_000_000.0,
            "longitude": lon_raw / 1_000_000.0,
            "satellites": satellites,
            "correctness": (status_byte >> 4) & 0x0F
        }

    @staticmethod
    def _decode_speed_direction(data: bytes) -> Dict[str, float]:
        if len(data) != 4:
             return {"error": "Invalid length for speed/dir"}

        speed_raw = struct.unpack('<H', data[0:2])[0]
        dir_raw = struct.unpack('<H', data[2:4])[0]
        
        return {
            "speed_kmh": speed_raw / 10.0,
            "direction_deg": dir_raw / 10.0
        }
