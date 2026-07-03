from prometheus_client import Gauge, Counter

class MercuryMetrics:
    def __init__(self):
        # Labels common to all metrics (mercury_id и container_id опциональные)
        self.labels = ['imei', 'mercury_id', 'container_id']

        # Enters (Inputs)
        self.enter_voltage = Gauge('galileosky_enter_voltage', 'Voltage on inputs', self.labels + ['input_id'])

        # Thermometers
        self.temperature = Gauge('galileosky_temperature', 'Temperature from thermometers', self.labels + ['sensor_id'])

        # Mercury Status
        self.mercury_status = Gauge('galileosky_mercury_status', 'Mercury meter status', self.labels)

        # Frequency
        self.mercury_frequency = Gauge('galileosky_mercury_frequency', 'Grid frequency', self.labels)

        # Voltage (Phase 1, 2, 3)
        self.mercury_voltage = Gauge('galileosky_mercury_voltage', 'Phase voltage', self.labels + ['phase'])

        # Current (Phase 1, 2, 3)
        self.mercury_current = Gauge('galileosky_mercury_current', 'Phase current', self.labels + ['phase'])

        # Angles between phases
        self.mercury_angle = Gauge('galileosky_mercury_angle', 'Angle between phases', self.labels + ['phase_pair'])

        # Active Power (Phase 1, 2, 3, Sum)
        self.mercury_active_power = Gauge('galileosky_mercury_active_power', 'Active power', self.labels + ['phase'])

        # Active Energy Forward
        self.mercury_active_energy_fwd = Gauge('galileosky_mercury_active_energy_fwd', 'Active energy forward', self.labels)

        # Power Factor (Phase 1, 2, 3, Sum)
        self.mercury_power_factor = Gauge('galileosky_mercury_power_factor', 'Power factor', self.labels + ['phase'])

        # Distortion (Phase 1, 2, 3)
        self.mercury_distortion = Gauge('galileosky_mercury_distortion', 'Harmonic distortion', self.labels + ['phase'])

        # Modbus (расширенные теги 0xFE): значение порта с привязкой к container_id
        self.modbus = Gauge('galileosky_modbus', 'Modbus port value', ['imei', 'container_id', 'modbus'])
        # Последний набор label'ов по каждому порту — чтобы убирать устаревшую
        # серию при смене container_id на лету (без перезапуска сервиса).
        self._modbus_last_labels: dict = {}

    def update_modbus(self, imei: str, modbus_id: str, container_id: str, value: float):
        """
        Обновить метрику Modbus-порта.
        :param modbus_id: номер порта (например "0" для modbus0)
        :param container_id: номер контейнера из карты привязки
        :param value: значение порта (уже поделённое на 100 в декодере)
        """
        labels = (imei, container_id, modbus_id)  # порядок: imei, container_id, modbus
        prev = self._modbus_last_labels.get(modbus_id)
        if prev is not None and prev != labels:
            # container_id порта поменяли на лету — удаляем старую серию,
            # чтобы в метриках не висело устаревшее значение под прежним контейнером
            try:
                self.modbus.remove(*prev)
            except KeyError:
                pass
        self.modbus.labels(*labels).set(value)
        self._modbus_last_labels[modbus_id] = labels

    def update(self, imei: str, data: dict, mercury_id: str = "none", container_id: str = "unknown"):
        """
        Update metrics with data from the parsed packet.
        :param imei: Device IMEI
        :param mercury_id: Mercury meter ID
        :param data: Dictionary with parsed data (similar to what is saved to JSONL)
        """
        common_labels = {'imei': imei, 'mercury_id': mercury_id, "container_id": container_id}

        # Enters
        for i in range(4):
            key = f"enter{i}"
            if key in data:
                self.enter_voltage.labels(**common_labels, input_id=str(i)).set(data[key])

        # Temperatures
        for i in range(8):
            key = f"galileosky_temp{i}"
            if key in data:
                self.temperature.labels(**common_labels, sensor_id=str(i)).set(data[key])

        # Mercury Status
        if "galileosky_mercury_state" in data:
            self.mercury_status.labels(**common_labels).set(data["galileosky_mercury_state"])

        # Frequency
        if "galileosky_mercury_f" in data:
            self.mercury_frequency.labels(**common_labels).set(data["galileosky_mercury_f"])

        # Voltage
        for i, key in enumerate(["galileosky_mercury_u1", "galileosky_mercury_u2", "galileosky_mercury_u3"], 1):
            if key in data:
                self.mercury_voltage.labels(**common_labels, phase=str(i)).set(data[key])

        # Current
        for i, key in enumerate(["galileosky_mercury_i1", "galileosky_mercury_i2", "galileosky_mercury_i3"], 1):
            if key in data:
                self.mercury_current.labels(**common_labels, phase=str(i)).set(data[key])

        # Angles
        angle_map = {
            "galileosky_mercury_a12": "1-2",
            "galileosky_mercury_a23": "2-3",
            "galileosky_mercury_a13": "1-3"
        }
        for key, pair in angle_map.items():
            if key in data:
                self.mercury_angle.labels(**common_labels, phase_pair=pair).set(data[key])

        # Active Power
        power_map = {
            "galileosky_mercury_p1": "1",
            "galileosky_mercury_p2": "2",
            "galileosky_mercury_p3": "3",
            "galileosky_mercury_ps": "sum",
            "galileosky_mercury_ps_legacy": "legacy_sum"
        }
        for key, phase in power_map.items():
            if key in data:
                self.mercury_active_power.labels(**common_labels, phase=phase).set(data[key])

        # Active Energy Forward
        if "galileosky_mercury_pa_plus" in data:
            self.mercury_active_energy_fwd.labels(**common_labels).set(data["galileosky_mercury_pa_plus"])

        # Power Factor
        pf_map = {
            "galileosky_mercury_ks1": "1",
            "galileosky_mercury_ks2": "2",
            "galileosky_mercury_ks3": "3",
            "galileosky_mercury_kss": "sum"
        }
        for key, phase in pf_map.items():
            if key in data:
                self.mercury_power_factor.labels(**common_labels, phase=phase).set(data[key])

        # Distortion
        for i, key in enumerate(["galileosky_mercury_kg1", "galileosky_mercury_kg2", "galileosky_mercury_kg3"], 1):
            if key in data:
                self.mercury_distortion.labels(**common_labels, phase=str(i)).set(data[key])

metrics = MercuryMetrics()
