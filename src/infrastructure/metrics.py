from prometheus_client import Gauge, Counter

class MercuryMetrics:
    def __init__(self):
        # Labels common to all metrics
        self.labels = ['imei', 'mercury_id']

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

    def update(self, imei: str, mercury_id: str, data: dict):
        """
        Update metrics with data from the parsed packet.
        :param imei: Device IMEI
        :param mercury_id: Mercury meter ID
        :param data: Dictionary with parsed data (similar to what is saved to JSONL)
        """
        common_labels = {'imei': imei, 'mercury_id': mercury_id}

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
            "galileosky_mercury_ps": "sum"
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
