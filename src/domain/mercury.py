from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Mercury230Data:
    address: int
    status: int
    reactive_power_sum: float
    reactive_power_p1: float
    reactive_power_p2: float
    reactive_power_p3: float
    active_power_sum: float
    active_power_p1: float
    active_power_p2: float
    active_power_p3: float
    angle_1_2: float
    angle_2_3: float
    angle_1_3: float
    voltage_p1: Optional[float]
    voltage_p2: Optional[float]
    voltage_p3: Optional[float]
    current_p1: float
    current_p2: float
    current_p3: float
    power_factor_sum: float
    power_factor_p1: float
    power_factor_p2: float
    power_factor_p3: float
    distortion_p1: float
    distortion_p2: float
    distortion_p3: float
    frequency: float
    temperature: int
    energy_active_fwd: float
    energy_active_rev: float
    energy_reactive_fwd: float
    energy_reactive_rev: float

class Mercury230Decoder:
    """
    Декодер данных счетчика Меркурий 230 AR-03 R.
    """

    @staticmethod
    def decode(data: List[int]) -> Optional[Mercury230Data]:
        if len(data) != 93:
            return None
        
        # 0:
        if data[0] != 0x02:
            return None # Not Mercury data or unknown format

        address = data[1]
        status = data[2]

        # 3-14: Reactive Powers
        r_sum = Mercury230Decoder._parse_power_3byte(data[3:6])
        r_p1 = Mercury230Decoder._parse_power_3byte(data[6:9])
        r_p2 = Mercury230Decoder._parse_power_3byte(data[9:12])
        r_p3 = Mercury230Decoder._parse_power_3byte(data[12:15])

        # 15-26: Active Powers
        a_sum = Mercury230Decoder._parse_power_3byte(data[15:18])
        a_p1 = Mercury230Decoder._parse_power_3byte(data[18:21])
        a_p2 = Mercury230Decoder._parse_power_3byte(data[21:24])
        a_p3 = Mercury230Decoder._parse_power_3byte(data[24:27])

        # 27-35: Angles
        ang_12 = Mercury230Decoder._parse_value_3byte_swap23(data[27:30]) / 100.0
        ang_23 = Mercury230Decoder._parse_value_3byte_swap23(data[30:33]) / 100.0
        ang_13 = Mercury230Decoder._parse_value_3byte_swap23(data[33:36]) / 100.0

        # 36-44: Voltages
        v_p1 = Mercury230Decoder._parse_value_3byte_swap23(data[36:39]) / 100.0
        v_p2 = Mercury230Decoder._parse_value_3byte_swap23(data[39:42]) / 100.0
        v_p3 = Mercury230Decoder._parse_value_3byte_swap23(data[42:45]) / 100.0

        # 45-53: Currents
        c_p1 = Mercury230Decoder._parse_value_3byte_swap23(data[45:48]) / 1000.0
        c_p2 = Mercury230Decoder._parse_value_3byte_swap23(data[48:51]) / 1000.0
        c_p3 = Mercury230Decoder._parse_value_3byte_swap23(data[51:54]) / 1000.0

        # 54-65: Power Factors
        pf_sum = Mercury230Decoder._parse_power_factor_3byte(data[54:57])
        pf_p1 = Mercury230Decoder._parse_power_factor_3byte(data[57:60])
        pf_p2 = Mercury230Decoder._parse_power_factor_3byte(data[60:63])
        pf_p3 = Mercury230Decoder._parse_power_factor_3byte(data[63:66])

        # 66-71: Distortion
        d_p1 = Mercury230Decoder._parse_value_2byte_swap(data[66:68]) / 100.0
        d_p2 = Mercury230Decoder._parse_value_2byte_swap(data[68:70]) / 100.0
        d_p3 = Mercury230Decoder._parse_value_2byte_swap(data[70:72]) / 100.0

        # 72-74: Frequency
        freq = Mercury230Decoder._parse_value_3byte_swap23(data[72:75]) / 100.0

        # 75-76: Temperature
        temp = Mercury230Decoder._parse_value_2byte_swap(data[75:77])

        # 77-92: Energies
        en_a_fwd = Mercury230Decoder._parse_energy_4byte(data[77:81])
        en_a_rev = Mercury230Decoder._parse_energy_4byte(data[81:85])
        en_r_fwd = Mercury230Decoder._parse_energy_4byte(data[85:89])
        en_r_rev = Mercury230Decoder._parse_energy_4byte(data[89:93])

        return Mercury230Data(
            address=address, status=status,
            reactive_power_sum=r_sum, reactive_power_p1=r_p1, reactive_power_p2=r_p2, reactive_power_p3=r_p3,
            active_power_sum=a_sum, active_power_p1=a_p1, active_power_p2=a_p2, active_power_p3=a_p3,
            angle_1_2=ang_12, angle_2_3=ang_23, angle_1_3=ang_13,
            voltage_p1=v_p1, voltage_p2=v_p2, voltage_p3=v_p3,
            current_p1=c_p1, current_p2=c_p2, current_p3=c_p3,
            power_factor_sum=pf_sum, power_factor_p1=pf_p1, power_factor_p2=pf_p2, power_factor_p3=pf_p3,
            distortion_p1=d_p1, distortion_p2=d_p2, distortion_p3=d_p3,
            frequency=freq, temperature=temp,
            energy_active_fwd=en_a_fwd, energy_active_rev=en_a_rev,
            energy_reactive_fwd=en_r_fwd, energy_reactive_rev=en_r_rev
        )

    @staticmethod
    def _parse_power_factor_3byte(b: List[int]) -> float:
        # Байт 0: Флаги / Статус
        # Байт 1, 2: Значение
        val = (b[2] << 8) | b[1]
        return val / 1000.0

    @staticmethod
    def _parse_power_3byte(b: List[int]) -> float:
        val = (b[2] << 8) | b[1]
        return val / 100.0

    @staticmethod
    def _parse_value_3byte_swap23(b: List[int]) -> int:
        return (b[0] << 16) | (b[2] << 8) | b[1]

    @staticmethod
    def _parse_value_2byte_swap(b: List[int]) -> int:
        return (b[1] << 8) | b[0]

    @staticmethod
    def _parse_energy_4byte(b: List[int]) -> float:
        val = (b[1] << 24) | (b[0] << 16) | (b[3] << 8) | b[2]
        return val / 1000.0 # kW/h
