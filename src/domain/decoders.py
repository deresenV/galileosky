import struct
from typing import List, Any, Dict, Union
from src.domain.mercury import Mercury230Decoder


def _build_extended_tag_lengths() -> Dict[int, int]:
    """
    Длины значений расширенных тегов (номер тега -> длина значения в байтах).
    Расширенные теги передаются внутри тега 0xFE как последовательность
    [2 байта номера тега (LE)] + [значение]. Длина значения определяется
    номером тега (см. протокол Galileosky, раздел "Расширенные теги").
    """
    lengths: Dict[int, int] = {}

    # Modbus 0..31  -> 0x0001..0x0020 (значение / 100)
    for t in range(0x0001, 0x0020 + 1):
        lengths[t] = 4
    # Bluetooth 0..63 -> 0x0021..0x0060
    for t in range(0x0021, 0x0060 + 1):
        lengths[t] = 4
    # Modbus 32..63 -> 0x0061..0x0080 (значение / 100)
    for t in range(0x0061, 0x0080 + 1):
        lengths[t] = 4

    lengths.update({
        0x0081: 2,   # Идентификатор соты (CID)
        0x0082: 2,   # Код локальной зоны (LAC)
        0x0083: 2,   # Код страны (MCC)
        0x0084: 2,   # Код оператора (MNC)
        0x0085: 1,   # RSSI
    })
    # Расширенные значения датчиков температуры 0..7 -> 0x0086..0x008D
    for t in range(0x0086, 0x008D + 1):
        lengths[t] = 4
    # Информация о спутниках GPS/GLONASS/BEIDOU/GALILEO -> 0x008E..0x0091
    for t in range(0x008E, 0x0091 + 1):
        lengths[t] = 4
    lengths.update({
        0x0092: 15,  # IMSI активной SIM
        0x0093: 1,   # Текущий слот SIM
        0x0094: 20,  # CCID активной SIM
        0x0095: 4,   # Идентификатор соты (CID) расширенный
        0x00A4: 1,   # Статус WiFi модема
        0x00A5: 1,   # Код ошибки WiFi
        0x00A6: 1,   # Статус GSM модема
        0x00A7: 1,   # Статус регистрации в сети
        0x00A8: 1,   # Статус GPRS
        0x00A9: 4,   # Свободная оперативная память
        0x00AB: 12,  # Статус записей в архиве
        0x00AC: 4,   # Номер последней записи в архиве
        0x00AD: 6,   # MAC адрес WiFi
        0x00AE: 6,   # MAC адрес BLE
        0x00AF: 14,  # Самодиагностика
        0x00B0: 1,   # Общий средний SNR
        0x00B1: 1,   # Статус SD карты
        0x00B2: 1,   # Ошибки SD карты
        0x00B3: 12,  # Статус архива сборщика
        0x00B4: 6,   # MAC адрес клиента 1
        0x00B5: 6,   # MAC адрес клиента 2
        0x00B6: 6,   # MAC адрес клиента 3
    })
    # Колесные датчики СКД 0..33 -> 0x00D9..0x00FA
    for t in range(0x00D9, 0x00FA + 1):
        lengths[t] = 3
    lengths.update({
        0x00FC: 1,   # Причина записи точки в архив
        0x00FD: 8,   # Тег iButton64
        0x00FE: 8,   # Тег iButton64 (2)
    })
    return lengths


def _build_modbus_ext_tags() -> Dict[int, int]:
    """Номер расширенного тега -> индекс Modbus-порта (Modbus N, N = 0..63)."""
    modbus: Dict[int, int] = {}
    for n in range(0, 32):          # Modbus 0..31  -> 0x0001..0x0020
        modbus[0x0001 + n] = n
    for n in range(32, 64):         # Modbus 32..63 -> 0x0061..0x0080
        modbus[0x0061 + (n - 32)] = n
    return modbus


# Карты расширенных тегов (тег 0xFE)
EXTENDED_TAG_LENGTHS: Dict[int, int] = _build_extended_tag_lengths()
MODBUS_EXT_TAGS: Dict[int, int] = _build_modbus_ext_tags()


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
            elif tag_num in (0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77):  # Термометры
                return TagDecoder._decode_thermometer(byte_data)
            elif tag_num == 0xD4:  # Пробег
                return TagDecoder._decode_uint32(byte_data)
            elif tag_num == 0xEA: # Массив пользователя (Меркурий 230?)
                 # Пытаемся декодировать как Меркурий
                 mercury_data = Mercury230Decoder.decode(data)
                 if mercury_data:
                     return mercury_data
                 return f"Raw: {byte_data.hex().upper()}"
            elif tag_num == 0xFE: # Расширенные теги (в т.ч. Modbus-порты)
                 return TagDecoder._decode_extended_tags(data)
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

    @staticmethod
    def _decode_thermometer(data: bytes) -> Dict[str, Union[int, str, None]]:
        if len(data) != 2:
            return {"error": "Invalid length for thermometer"}
        
        # Байт 0: ID (unsigned)
        thermometer_id = data[0]
        # Байт 1: Температура (signed)
        temperature_raw = struct.unpack('<b', data[1:2])[0]
        
        # Проверка на обрыв
        if thermometer_id == 127 and temperature_raw == -128:
            return {
                "id": thermometer_id, 
                "temperature": None, 
                "status": "break"
            }
            
        return {
            "id": thermometer_id,
            "temperature": temperature_raw,
            "status": "ok"
        }

    @staticmethod
    def _decode_extended_tags(data: List[int]) -> Dict[str, Any]:
        """
        Декодирует содержимое тега 0xFE (расширенные теги).

        Структура: последовательность [2 байта номера тега (LE)] + [значение],
        длина значения определяется номером тега (EXTENDED_TAG_LENGTHS).

        Modbus-порты (0..63) декодируются в ключи modbus0..modbus63 как знаковое
        32-битное целое (LE), делённое на 100. Остальные известные расширенные
        теги сохраняются как сырой hex под ключом вида "0xXXXX".

        Если встречен неизвестный тег (длину определить нельзя) — парсинг
        останавливается, а необработанный остаток сохраняется в ключе "_unparsed".
        """
        result: Dict[str, Any] = {}
        i = 0
        n = len(data)

        while i + 2 <= n:
            ext_num = data[i] | (data[i + 1] << 8)
            length = EXTENDED_TAG_LENGTHS.get(ext_num)

            if length is None:
                # Длина неизвестного тега неизвестна — дальше двигаться нельзя
                result["_unparsed"] = bytes(data[i:]).hex().upper()
                break

            value_start = i + 2
            if value_start + length > n:
                result["_error"] = f"Not enough data for ext tag 0x{ext_num:04X}"
                break

            value_bytes = data[value_start:value_start + length]
            i = value_start + length

            if ext_num in MODBUS_EXT_TAGS:
                raw = struct.unpack('<i', bytes(value_bytes))[0]
                result[f"modbus{MODBUS_EXT_TAGS[ext_num]}"] = raw / 100.0
            else:
                result[f"0x{ext_num:04X}"] = bytes(value_bytes).hex().upper()

        return result
