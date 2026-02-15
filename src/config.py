import os
from dataclasses import dataclass

@dataclass
class Config:
    HOST: str = os.getenv("GALILEOSKY_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("GALILEOSKY_PORT", 12347))
    TIMEOUT: int = int(os.getenv("GALILEOSKY_TIMEOUT", 60))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

config = Config()
