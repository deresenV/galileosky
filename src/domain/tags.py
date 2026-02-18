from typing import Dict, ClassVar, Optional

class Tag:
    def __init__(self, num_byte: int, tag: str, length: int, description: str):
        self.num = num_byte
        self.tag_hex_str = tag
        self.length = length
        self.description = description

class Tags:
    # Определение тегов как атрибутов класса для удобного доступа
    x10 = Tag(num_byte=0x10, tag="0x10", length=2, description="Номер записи в архиве")
    x20 = Tag(num_byte=0x20, tag="0x20", length=4, description="Дата и время (Unix time)")
    x21 = Tag(num_byte=0x21, tag="0x21", length=2, description="Миллисекунды")
    x30 = Tag(num_byte=0x30, tag="0x30", length=9, description="Координаты в градусах, количество спутников, статус координат")
    x33 = Tag(num_byte=0x33, tag="0x33", length=4, description="Скорость/направление")
    x34 = Tag(num_byte=0x34, tag="0x34", length=2, description="Высота")
    x35 = Tag(num_byte=0x35, tag="0x35", length=1, description="HDOP")
    x40 = Tag(num_byte=0x40, tag="0x40", length=2, description="Статус устройства")
    x41 = Tag(num_byte=0x41, tag="0x41", length=2, description="Напряжение питания (мВ)")
    x42 = Tag(num_byte=0x42, tag="0x42", length=2, description="Напряжение АКБ (мВ)")
    x43 = Tag(num_byte=0x43, tag="0x43", length=1, description="Температура терминала (°C)")
    x45 = Tag(num_byte=0x45, tag="0x45", length=2, description="Состояние выхода")
    x46 = Tag(num_byte=0x46, tag="0x46", length=2, description="Сработка на соответсвующем типе")
    x48 = Tag(num_byte=0x48, tag="0x48", length=2, description="Расширенный статус")
    x49 = Tag(num_byte=0x49, tag="0x49", length=1, description="Канал передачи")
    x50 = Tag(num_byte=0x50, tag="0x50", length=2, description="Вход 0 (мВ)")
    x51 = Tag(num_byte=0x51, tag="0x51", length=2, description="Вход 1 (мВ)")
    x52 = Tag(num_byte=0x52, tag="0x52", length=2, description="Вход 2 (мВ)")
    x53 = Tag(num_byte=0x53, tag="0x53", length=2, description="Вход 3 (мВ)")
    x54 = Tag(num_byte=0x54, tag="0x54", length=2, description="Вход 4 (мВ)")
    x55 = Tag(num_byte=0x55, tag="0x55", length=2, description="Вход 5 (мВ)")
    
    # Теги с переменной длиной или особыми форматами
    xEA = Tag(num_byte=0xEA, tag="0xEA", length=1, description="Массив данных пользователя (длина указана в следующем байте)")
    xFE = Tag(num_byte=0xFE, tag="0xFE", length=2, description="Расширенные теги (длина данных указана в следующих байтах)")
    xD4 = Tag(num_byte=0xD4, tag="0xD4", length=4, description="Общий пробег по GPS (м)")
    x63 = Tag(num_byte=0x63, tag="0x63", length=3, description="RS485[3] (ДУТ адрес 3)")
    x70 = Tag(num_byte=0x70, tag="0x70", length=2, description="Идентификатор термометра 0 и измеренная температура, °C")
    x71 = Tag(num_byte=0x71, tag="0x71", length=2, description="Идентификатор термометра 1 и измеренная температура, °C")
    x72 = Tag(num_byte=0x71, tag="0x72", length=2, description="Идентификатор термометра 2 и измеренная температура, °C")
    x73 = Tag(num_byte=0x71, tag="0x73", length=2, description="Идентификатор термометра 3 и измеренная температура, °C")
    x74 = Tag(num_byte=0x71, tag="0x74", length=2, description="Идентификатор термометра 4 и измеренная температура, °C")
    x75 = Tag(num_byte=0x71, tag="0x75", length=2, description="Идентификатор термометра 5 и измеренная температура, °C")
    x76 = Tag(num_byte=0x71, tag="0x75", length=2, description="Идентификатор термометра 5 и измеренная температура, °C")
    x77 = Tag(num_byte=0x71, tag="0x75", length=2, description="Идентификатор термометра 5 и измеренная температура, °C")

    # Словарь для поиска по байту
    ALL_TAGS: ClassVar[Dict[int, Tag]] = {
        0x10: x10, 0x20: x20, 0x21: x21, 0x30: x30, 0x33: x33, 0x34: x34, 0x35: x35,
        0x40: x40, 0x41: x41, 0x42: x42, 0x43: x43, 0x45: x45, 0x46: x46, 0x48: x48, 0x49: x49,
        0x50: x50, 0x51: x51, 0x52: x52, 0x53: x53, 0x54: x54, 0x55: x55,
        0xEA: xEA, 0xFE: xFE, 0xD4: xD4, 0x63: x63,
        0x70: x70, 0x71: x71, 0x72: x72, 0x73: x73, 0x74: x74, 0x75:x75, 0x76: x76, 0x77: x77
    }

    @classmethod
    def get_tag(cls, byte_val: int) -> Optional[Tag]:
        return cls.ALL_TAGS.get(byte_val)
