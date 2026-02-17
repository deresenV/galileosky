import json
from math import sqrt

import aiofiles
from datetime import datetime
from typing import Dict, Any, Optional
from src.domain.interfaces import IStorage
from src.domain.mercury import Mercury230Data


def normalize_energy(value: float) -> Optional[float]:
    """Обработка специальных значений (0xFFFFFFFF / 1000 = 4294967.295 — признак отсутствия данных)"""
    # return None if abs(value - 4294967.295) < 0.001 else value

    return value

def normalize_power_factor(value: float) -> float:
    """Коррекция коэффициента мощности (ошибка масштабирования)"""
    # if value > 1.0 and abs(value - 4195.3) < 0.1:
    #     return round(value / 4096, 3)
    # return min(round(value, 3), 1.0) if isinstance(value, (int, float)) else 1.0
    return value


def format_mercury_data(mercury_data: Mercury230Data, received_at: str, enters) -> Dict[str, Any]:
    """
    Форматирует объект данных счетчика Меркурий 230 в структурированный словарь,
    совместимый с метриками дашборда (плоская структура для удобства парсинга в Loki).
    Значения сохраняются в естественных единицах (В, А, Вт, Гц), без дополнительных множителей.
    """
    return {
        "0x45": enters["0x45"],
        "0x46": enters["0x46"],
        "enter0": int(enters["enter0"]),
        "enter1": int(enters["enter1"]),
        "enter2": int(enters["enter2"]),
        "enter3": int(enters["enter3"]),
        "_received_at": received_at,
        "mercury_id": str(mercury_data.address),  # addr для дашборда
        "imei": "869531073980322", # Placeholder, так как дашборд требует imei
        
        # Статусы
        "galileosky_mercury_state": mercury_data.status,
        
        # Частота (F)
        "galileosky_mercury_f": mercury_data.frequency,
        
        # Напряжения (U1, U2, U3)
        "galileosky_mercury_u1": mercury_data.voltage_p1 or 0,
        "galileosky_mercury_u2": mercury_data.voltage_p2 or 0,
        "galileosky_mercury_u3": mercury_data.voltage_p3 or 0,
        
        # Токи (I1, I2, I3)
        "galileosky_mercury_i1": mercury_data.current_p1,
        "galileosky_mercury_i2": mercury_data.current_p2,
        "galileosky_mercury_i3": mercury_data.current_p3,
        
        # Углы между фазами (A12, A23, A13)
        "galileosky_mercury_a12": mercury_data.angle_1_2,
        "galileosky_mercury_a23": mercury_data.angle_2_3,
        "galileosky_mercury_a13": mercury_data.angle_1_3,
        
        # Активная мощность по фазам и сумма (P1, P2, P3, PS)
        "galileosky_mercury_p1": mercury_data.active_power_p1,
        "galileosky_mercury_p2": mercury_data.active_power_p2,
        "galileosky_mercury_p3": mercury_data.active_power_p3,
        # "galileosky_mercury_ps": mercury_data.active_power_sum,
        "galileosky_mercury_ps": (float(mercury_data.current_p1)*float(mercury_data.voltage_p1)*float(mercury_data.power_factor_p1)+
        float(mercury_data.current_p2)*float(mercury_data.voltage_p2)*float(mercury_data.power_factor_p2)+
        float(mercury_data.current_p3)*float(mercury_data.voltage_p3)*float(mercury_data.power_factor_p3))*300/1000,

        # Энергия (Active Forward) - для графиков накопленной энергии
        "galileosky_mercury_pa_plus": mercury_data.energy_active_fwd,
        
        # Коэффициенты мощности (KS1, KS2, KS3, KSS)
        "galileosky_mercury_ks1": mercury_data.power_factor_p1,
        "galileosky_mercury_ks2": mercury_data.power_factor_p2,
        "galileosky_mercury_ks3": mercury_data.power_factor_p3,
        "galileosky_mercury_kss": mercury_data.power_factor_sum,
        
        # Коэффициенты искажения (KG1, KG2, KG3)
        "galileosky_mercury_kg1": mercury_data.distortion_p1,
        "galileosky_mercury_kg2": mercury_data.distortion_p2,
        "galileosky_mercury_kg3": mercury_data.distortion_p3,
    }


class JsonFileStorage(IStorage):
    """
    Реализация хранилища, сохраняющая данные в JSON файл (формат JSON Lines).
    """

    def __init__(self, file_path: str = "parsed_data.jsonl"):
        self.file_path = file_path

    async def save(self, packet_data: Dict[str, Any]):
        tags = packet_data.get("tags", {})

        # Обработка только тега 0xEA (данные счетчика Меркурий)
        if "0xEA" in tags:
            try:
                mercury_obj = tags["0xEA"]
                
                # Безопасное получение значений входов (с дефолтным значением 0, если тег отсутствует)
                enter0 = tags.get("0x50", 0)
                enter1 = tags.get("0x51", 0)
                enter2 = tags.get("0x52", 0)
                enter3 = tags.get("0x53", 0)
                
                enters_data = {
                    "enter0": enter0,
                    "enter1": enter1,
                    "enter2": enter2,
                    "enter3": enter3,
                    "0x45": tags.get("0x45", 0),
                    "0x46": tags.get("0x46", 0),
                }
                # Проверяем, что это объект Mercury230Data
                if not isinstance(mercury_obj, Mercury230Data):
                    # Если вдруг пришла строка или байты, попробуем залогировать как ошибку или пропустить
                    raise ValueError(f"Expected Mercury230Data, got {type(mercury_obj)}")

                received_at = datetime.now().isoformat()
                
                # Форматирование данных
                formatted_data = format_mercury_data(mercury_obj, received_at, enters_data)
                
                # Добавляем IMEI, если он есть в пакете (в будущем)
                # formatted_data["imei"] = packet_data.get("imei", "unknown")

                # Сохранение в файл (JSON Lines)
                json_line = json.dumps(formatted_data, ensure_ascii=False)
                async with aiofiles.open(self.file_path, mode='a', encoding='utf-8') as f:
                    await f.write(json_line + "\n")

            except Exception as e:
                # Логирование ошибки
                error_data = {
                    "_received_at": datetime.now().isoformat(),
                    "error": str(e),
                    "raw_data": str(tags.get("0xEA"))
                }
                json_line = json.dumps(error_data, ensure_ascii=False)
                async with aiofiles.open(self.file_path.replace('.jsonl', '_errors.jsonl'),
                                         mode='a', encoding='utf-8') as f:
                    await f.write(json_line + "\n")