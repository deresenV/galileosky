import os
from dataclasses import dataclass

@dataclass
class Config:
    HOST: str = os.getenv("GALILEOSKY_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("GALILEOSKY_PORT", 12347))
    TIMEOUT: int = int(os.getenv("GALILEOSKY_TIMEOUT", 60))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    cont_ids = {
        "99": "1",
        "73": "2",
        "22": "3",
        "89": "4",
        "77": "5",
        "95": "6",
        "94": "7",
        "92": "8",
        "27": "9",
        "68": "10",
        "41": "11",
        "2": "13",
    }

config = Config()
