from typing import List
from src.infrastructure.file_reader import LocalFileReader
from src.application.hex_service import HexProcessingService
from src.domain.parser import TagParser
from src.domain.decoders import TagDecoder
from src.domain.mercury import Mercury230Data

def convert_file_to_hex(file_path: str) -> List[int]:
    """
    Функция для конвертации файла с raw-code в hex-массив.
    """
    reader = LocalFileReader()
    service = HexProcessingService(reader)
    return service.process_file(file_path)

def parse_and_print_tags(byte_data: List[int]):
    """
    Парсит и выводит теги с декодированными значениями.
    """
    parser = TagParser()
    result = parser.parse(byte_data)
    
    # print(f"\nНайдено тегов: {len(result.tags)}")
    # print(f"Пропущено байтов: {len(result.skipped_bytes)}")
    #
    # print("\nДетализация по тегам:")
    # print("-" * 100)
    # print(f"{'Tag':<6} | {'Description':<50} | {'Raw Hex':<20} | {'Decoded Value'}")
    # print("-" * 100)
    #
    for parsed_tag in result.tags:
        # # Декодирование значения
        decoded_value = TagDecoder.decode(parsed_tag.tag.num, parsed_tag.data)
        #
        # # Форматирование вывода
        # raw_hex = " ".join(f"{b:02X}" for b in parsed_tag.data)
        # # Обрезаем длинный hex
        # raw_hex_short = raw_hex
        # if len(raw_hex_short) > 20:
        #     raw_hex_short = raw_hex_short[:17] + "..."
        #
        # print(f"{parsed_tag.tag.tag_hex_str:<6} | {parsed_tag.tag.description[:50]:<50} | {raw_hex_short:<20} | {decoded_value if not isinstance(decoded_value, Mercury230Data) else 'Mercury Data (see below)'}")
        #
        if isinstance(decoded_value, Mercury230Data):
            # print("  >>> Данные Mercury 230:")
            # print(f"      Адрес: {decoded_value.address}, Статус: {decoded_value.status}")
            print(f"      Активная мощность (Вт): Сумма={decoded_value.active_power_sum}, P1={decoded_value.active_power_p1}, P2={decoded_value.active_power_p2}, P3={decoded_value.active_power_p3}")
            print(f"      Реактивная мощность (ВАр): Сумма={decoded_value.reactive_power_sum}, P1={decoded_value.reactive_power_p1}, P2={decoded_value.reactive_power_p2}, P3={decoded_value.reactive_power_p3}")
            print(f"      Напряжение (В): P1={decoded_value.voltage_p1}, P2={decoded_value.voltage_p2}, P3={decoded_value.voltage_p3}")
            print(f"      Ток (А): P1={decoded_value.current_p1}, P2={decoded_value.current_p2}, P3={decoded_value.current_p3}")
            print(f"      Частота: {decoded_value.frequency} Гц, Температура: {decoded_value.temperature} °C")
            print(f"      Энергия (кВт·ч/кВАр·ч): A+={decoded_value.energy_active_fwd}, A-={decoded_value.energy_active_rev}, R+={decoded_value.energy_reactive_fwd}, R-={decoded_value.energy_reactive_rev}")
            print("-" * 100)

if __name__ == "__main__":
    example_path = "/Users/arsenijsojkin/PycharmProjects/GalileoskyTenParser/template.txt"
    try:
        byte_data = convert_file_to_hex(example_path)
        parse_and_print_tags(byte_data)
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
