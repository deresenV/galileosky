import json
import aiofiles
from datetime import datetime
from typing import Dict, Any, Optional
from src.domain.interfaces import IStorage
from src.domain.mercury import Mercury230Data


def normalize_energy(value: float) -> Optional[float]:
    """Обработка специальных значений (0xFFFFFFFF / 1000 = 4294967.295 — признак отсутствия данных)"""
    return None if abs(value - 4294967.295) < 0.001 else value


def normalize_power_factor(value: float) -> float:
    """Коррекция коэффициента мощности (ошибка масштабирования)"""
    if value > 1.0 and abs(value - 4195.3) < 0.1:
        return round(value / 4096, 3)
    return min(round(value, 3), 1.0) if isinstance(value, (int, float)) else 1.0


def format_mercury_data(mercury_data: Mercury230Data, received_at: str) -> Dict[str, Any]:
    """
    Форматирует объект данных счетчика Меркурий 230 в структурированный словарь.
    """
    return {
        "_received_at": received_at,
        "metadata": {
            "address": mercury_data.address,
            "status": mercury_data.status,
            "status_description": "Норма" if mercury_data.status == 0 else f"Код {mercury_data.status}"
        },
        "power": {
            "active": {
                "sum_w": round(mercury_data.active_power_sum, 2),
                "phase1_w": round(mercury_data.active_power_p1, 2),
                "phase2_w": round(mercury_data.active_power_p2, 2),
                "phase3_w": round(mercury_data.active_power_p3, 2)
            },
            "reactive": {
                "sum_var": round(mercury_data.reactive_power_sum, 2),
                "phase1_var": round(mercury_data.reactive_power_p1, 2),
                "phase2_var": round(mercury_data.reactive_power_p2, 2),
                "phase3_var": round(mercury_data.reactive_power_p3, 2)
            },
            "power_factor": {
                "sum": normalize_power_factor(mercury_data.power_factor_sum),
                "phase1": normalize_power_factor(mercury_data.power_factor_p1),
                "phase2": normalize_power_factor(mercury_data.power_factor_p2),
                "phase3": normalize_power_factor(mercury_data.power_factor_p3)
            }
        },
        "network": {
            "voltage": {
                "phase1_v": round(mercury_data.voltage_p1, 2) if mercury_data.voltage_p1 is not None else 0,
                "phase2_v": round(mercury_data.voltage_p2, 2) if mercury_data.voltage_p2 is not None else 0,
                "phase3_v": round(mercury_data.voltage_p3, 2) if mercury_data.voltage_p3 is not None else 0
            },
            "current": {
                "phase1_a": round(mercury_data.current_p1, 3),
                "phase2_a": round(mercury_data.current_p2, 3),
                "phase3_a": round(mercury_data.current_p3, 3)
            },
            "phase_angles_deg": {
                "phase1_2": round(mercury_data.angle_1_2, 2),
                "phase2_3": round(mercury_data.angle_2_3, 2),
                "phase1_3": round(mercury_data.angle_1_3, 2)
            },
            "distortion_kg": {
                "phase1": round(mercury_data.distortion_p1, 3),
                "phase2": round(mercury_data.distortion_p2, 3),
                "phase3": round(mercury_data.distortion_p3, 3)
            },
            "frequency_hz": round(mercury_data.frequency, 2),
            "temperature_c": mercury_data.temperature
        },
        "energy": {
            "active_forward_kwh": round(mercury_data.energy_active_fwd, 3),
            "active_reverse_kwh": normalize_energy(mercury_data.energy_active_rev),
            "reactive_forward_kvah": round(mercury_data.energy_reactive_fwd, 3),
            "reactive_reverse_kvah": normalize_energy(mercury_data.energy_reactive_rev)
        }
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
                
                # Проверяем, что это объект Mercury230Data
                if not isinstance(mercury_obj, Mercury230Data):
                    # Если вдруг пришла строка или байты, попробуем залогировать как ошибку или пропустить
                    raise ValueError(f"Expected Mercury230Data, got {type(mercury_obj)}")

                received_at = datetime.now().isoformat()
                
                # Форматирование данных
                formatted_data = format_mercury_data(mercury_obj, received_at)

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