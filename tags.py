from typing import Dict, ClassVar


class Tag:
    def __init__(self, num_byte: int, tag: str, length: int, description: str):
        self.num = num_byte
        self.tag = tag
        self.length = length
        self.description = description

class Tags:
    # Справочник всех тегов
    ALL_TAGS: ClassVar[Dict[str, Tag]] = {}

    @classmethod
    def _add_tag(cls, tag_instance: Tag):
        cls.ALL_TAGS[tag_instance.tag] = tag_instance

    # Основные теги
    x10 = Tag(num_byte=0x10, tag="0x10", length=2, description="Номер записи в архиве")
    _add_tag(x10)

    x20 = Tag(num_byte=0x20, tag="0x20", length=4, description="Дата и время (Unix time)")
    _add_tag(x20)

    x21 = Tag(num_byte=0x21, tag="0x21", length=2, description="Миллисекунды")
    _add_tag(x21)

    x30 = Tag(num_byte=0x30, tag="0x30", length=9, description="Координаты в градусах, количество спутников, статус координат")
    _add_tag(x30)

    x33 = Tag(num_byte=0x33, tag="0x33", length=4, description="Скорость/направление")
    _add_tag(x33)

    x34 = Tag(num_byte=0x34, tag="0x34", length=2, description="Высота")
    _add_tag(x34)

    x35 = Tag(num_byte=0x35, tag="0x35", length=1, description="HDOP")
    _add_tag(x35)

    x40 = Tag(num_byte=0x40, tag="0x40", length=2, description="Статус устройства")
    _add_tag(x40)

    x41 = Tag(num_byte=0x41, tag="0x41", length=2, description="Напряжение питания (мВ)")
    _add_tag(x41)

    x42 = Tag(num_byte=0x42, tag="0x42", length=2, description="Напряжение АКБ (мВ)")
    _add_tag(x42)

    x43 = Tag(num_byte=0x43, tag="0x43", length=1, description="Температура терминала (°C)")
    _add_tag(x43)

    x48 = Tag(num_byte=0x48, tag="0x48", length=2, description="Расширенный статус")
    _add_tag(x48)

    x49 = Tag(num_byte=0x49, tag="0x49", length=1, description="Канал передачи")
    _add_tag(x49)

    x50 = Tag(num_byte=0x50, tag="0x50", length=2, description="Вход 0 (мВ)")
    _add_tag(x50)

    x51 = Tag(num_byte=0x51, tag="0x51", length=2, description="Вход 1 (мВ)")
    _add_tag(x51)

    x52 = Tag(num_byte=0x52, tag="0x52", length=2, description="Вход 2 (мВ)")
    _add_tag(x52)

    x53 = Tag(num_byte=0x53, tag="0x53", length=2, description="Вход 3 (мВ)")
    _add_tag(x53)

    x54 = Tag(num_byte=0x54, tag="0x54", length=2, description="Вход 4 (мВ)")
    _add_tag(x54)

    x55 = Tag(num_byte=0x55, tag="0x55", length=2, description="Вход 5 (мВ)")
    _add_tag(x55)

    # Теги с переменной длиной или особыми форматами
    # EA требует чтения длины из потока данных
    # FE также требует специальной обработки
    xEA = Tag(num_byte=0xEA, tag="0xEA", length=1, description="Массив данных пользователя (длина указана в следующем байте)")
    _add_tag(xEA)

    xFE = Tag(num_byte=0xFE, tag="0xFE", length=2, description="Расширенные теги (длина данных указана в следующих байтах)")
    _add_tag(xFE)

    xD4 = Tag(num_byte=0xD4, tag="0xD4", length=4, description="Общий пробег по GPS (м)")
    _add_tag(xD4)

    x63 = Tag(num_byte=0x63, tag="0x63", length=3, description="RS485[3] (ДУТ адрес 3)")
    _add_tag(x63)



# Получить конкретный тег
# tag_40 = Tags.x40
# print(f"Tag: {tag_40.tag}, Length: {tag_40.length}, Desc: {tag_40.description}")
#
# # Итерироваться по всем тегам
# print("\nAll Tags:")
# for tag_obj in Tags.ALL_TAGS.values():
#     print(f"  {tag_obj.tag}: {tag_obj.description} (Length: {tag_obj.length})")
#
# # Получить тег по строковому ключу
# print(f"\nTag '0x30': {Tags.ALL_TAGS['0x30'].description}")


