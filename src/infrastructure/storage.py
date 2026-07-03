import dataclasses
import json
import logging
from datetime import datetime
from typing import Dict, Any

from src.config import config
from src.domain.mercury import Mercury230Data
from src.infrastructure.metrics import metrics
from src.infrastructure.modbus_containers import modbus_containers

logger = logging.getLogger(__name__)


def _to_serializable(value: Any) -> Any:
    """
    Рекурсивно приводит распарсенное значение тега к JSON-сериализуемому виду.
    В частности разворачивает dataclass'ы (например 0xEA -> Mercury230Data) в dict
    со всеми полями.
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    if isinstance(value, dict):
        return {k: _to_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_serializable(v) for v in value]
    return value


def log_parsed_data(packet_data: Dict[str, Any]) -> None:
    """
    Записать распарсенные из тегов данные (как пришли от датчика) в файл (JSONL).
    Каждое сообщение — отдельная строка JSON: все теги, включая 0xEA (Mercury230Data)
    со всеми полями. Пишется в дополнение к метрикам.
    """
    try:
        record = {
            "_received_at": datetime.now().isoformat(),
            "source_ip": packet_data.get("source_ip"),
            "source_port": packet_data.get("source_port"),
            "tags": _to_serializable(packet_data.get("tags", {})),
        }
        with open(config.PARSED_DATA_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write parsed data to {config.PARSED_DATA_FILE}: {e}")

def format_mercury_data(mercury_data: Mercury230Data) -> Dict[str, Any]:
    return {
        "mercury_id": str(mercury_data.address),
        "container_id": config.cont_ids.get(str(mercury_data.address), "unknown"),
        "galileosky_mercury_coefficient": config.cont_coefficient.get(str(mercury_data.address), 300),
        "galileosky_mercury_state": mercury_data.status,
        "galileosky_mercury_f": mercury_data.frequency,
        "galileosky_mercury_u1": mercury_data.voltage_p1 or 0,
        "galileosky_mercury_u2": mercury_data.voltage_p2 or 0,
        "galileosky_mercury_u3": mercury_data.voltage_p3 or 0,
        "galileosky_mercury_i1": float(mercury_data.current_p1) * float(config.cont_coefficient.get(str(mercury_data.address), 300)),
        "galileosky_mercury_i2": float(mercury_data.current_p2) * float(config.cont_coefficient.get(str(mercury_data.address), 300)),
        "galileosky_mercury_i3": float(mercury_data.current_p3) * float(config.cont_coefficient.get(str(mercury_data.address), 300)),
        "galileosky_mercury_a12": mercury_data.angle_1_2,
        "galileosky_mercury_a23": mercury_data.angle_2_3,
        "galileosky_mercury_a13": mercury_data.angle_1_3,
        "galileosky_mercury_p1": mercury_data.active_power_p1,
        "galileosky_mercury_p2": mercury_data.active_power_p2,
        "galileosky_mercury_p3": mercury_data.active_power_p3,
        "galileosky_mercury_ps_legacy": mercury_data.active_power_sum,
        "galileosky_mercury_ps": (float(mercury_data.current_p1) * float(mercury_data.voltage_p1) * float(
            mercury_data.power_factor_p1) +
                                  float(mercury_data.current_p2) * float(mercury_data.voltage_p2) * float(
                    mercury_data.power_factor_p2) +
                                  float(mercury_data.current_p3) * float(mercury_data.voltage_p3) * float(
                    mercury_data.power_factor_p3)) / 1000 * float(config.cont_coefficient.get(str(mercury_data.address), 300)),
        "galileosky_mercury_pa_plus": mercury_data.energy_active_fwd,
        "galileosky_mercury_ks1": mercury_data.power_factor_p1,
        "galileosky_mercury_ks2": mercury_data.power_factor_p2,
        "galileosky_mercury_ks3": mercury_data.power_factor_p3,
        "galileosky_mercury_kss": mercury_data.power_factor_sum,
        "galileosky_mercury_kg1": mercury_data.distortion_p1,
        "galileosky_mercury_kg2": mercury_data.distortion_p2,
        "galileosky_mercury_kg3": mercury_data.distortion_p3,
    }


class MetricsStorage():
    """
    Хранилище метрик
    """
    def _get_temps(self, packet_data: Dict[str, Any]) -> Dict[str, Any]:
        tags = packet_data.get("tags", {})
        temps = {
            "galileosky_temp0": tags.get("0x70", 0),
            "galileosky_temp1": tags.get("0x71", 0),
            "galileosky_temp2": tags.get("0x72", 0),
            "galileosky_temp3": tags.get("0x73", 0),
            "galileosky_temp4": tags.get("0x74", 0),
            "galileosky_temp5": tags.get("0x75", 0),
            "galileosky_temp6": tags.get("0x76", 0),
            "galileosky_temp7": tags.get("0x77", 0)
        }
        for key, val in temps.items():
            if isinstance(val, dict) and "temperature" in val:
                temps[key] = val["temperature"] if val["temperature"] is not None else 0
            elif isinstance(val, dict) and "error" in val:
                temps[key] = 0
        return temps

    def _get_enters(self, packet_data: Dict[str, Any]) -> Dict[str, Any]:
        tags = packet_data.get("tags", {})
        enters = {
            "enter0": tags.get("0x50", 0),
            "enter1": tags.get("0x51", 0),
            "enter2": tags.get("0x52", 0),
            "enter3": tags.get("0x53", 0)
        }
        return enters

    def _get_container_id(self, mercury_id: str) -> Dict[str, str]:
        """Получение номера контейнера из id счетчика"""
        return {"container_id": config.cont_ids.get(mercury_id, "unknown")}

    def _get_received_at(self, received_at: str) -> Dict[str, str]:
        """Время получения данных"""
        return {"_received_at": received_at}

    #todo перенести на получение из mercury
    def _get_imei(self) -> Dict[str, str]:
        return {"imei": "869531073980322"}

    def _update_modbus_metrics(self, tags: Dict[str, Any], imei: str) -> None:
        """
        Выгрузить значения Modbus-портов (из расширенных тегов 0xFE) в метрики,
        проставив container_id по карте привязки (перечитывается на лету).
        """
        ext = tags.get("0xFE")
        if not isinstance(ext, dict):
            return
        for key, value in ext.items():
            if not key.startswith("modbus") or not isinstance(value, (int, float)):
                continue
            modbus_id = key[len("modbus"):]
            container_id = modbus_containers.get_container_id(key)
            try:
                metrics.update_modbus(
                    imei=imei,
                    modbus_id=modbus_id,
                    container_id=container_id,
                    value=value,
                )
            except Exception as e:
                logger.warning(f"Error updating modbus metric {key}: {e}", exc_info=True)

    async def save(self, packet_data: Dict[str, Any]):
        received_at = datetime.now().isoformat()
        tags = packet_data.get("tags", {})

        # Сохраняем сами распарсенные теги (как пришли от датчика), включая
        # 0xEA со всеми полями, в файл — в дополнение к метрикам.
        log_parsed_data(packet_data)

        enters = self._get_enters(packet_data)
        temps = self._get_temps(packet_data)
        imei = "869531073980322"

        # Modbus-порты (0xFE) -> метрики с container_id из карты привязки
        self._update_modbus_metrics(tags, imei)

        if "0xEA" in tags:
            logger.info("Found 0xEA tag, processing as Mercury data")
            try:
                mercury_obj = tags["0xEA"]
                if not isinstance(mercury_obj, Mercury230Data):
                    raise ValueError(f"Expected Mercury230Data, got {type(mercury_obj)}")

                mercury_data = format_mercury_data(mercury_obj)
                mercury_id = mercury_data["mercury_id"]
                container_id_val = mercury_data["container_id"]
                
                try:
                    metrics_data = {**mercury_data, **enters, **temps, "_received_at": received_at, "imei": imei}

                    for k, v in metrics_data.items():
                        if k.startswith("galileosky_") or k.startswith("enter"):
                            try:
                                if v is not None:
                                    metrics_data[k] = float(v)
                            except (ValueError, TypeError):
                                pass

                    metrics.update(
                        imei=imei,
                        data=metrics_data,
                        mercury_id=mercury_id,
                        container_id=container_id_val
                    )
                    logger.info(f"Successfully updated metrics for mercury_id {mercury_id}")
                except Exception as e:
                    logger.warning(f"Error updating metrics: {e}", exc_info=True)

            except Exception as e:
                logger.error(f"Error processing Mercury data: {e}", exc_info=True)
        else:
            try:
                metrics_data = {**enters, **temps, "_received_at": received_at, "imei": imei}

                for k, v in metrics_data.items():
                    if k.startswith("galileosky_") or k.startswith("enter"):
                        try:
                            if v is not None:
                                metrics_data[k] = float(v)
                        except (ValueError, TypeError):
                            pass

                metrics.update(
                    imei=imei,
                    data=metrics_data
                )
            except Exception as e:
                logger.error(f"Error processing without mercury data: {e}", exc_info=True)
