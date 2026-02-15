from typing import List
from dataclasses import dataclass
from src.domain.tags import Tag

@dataclass
class ParsedTag:
    """
    Модель данных распарсенного тега.
    """
    tag: Tag
    data: List[int]
    
    def __repr__(self):
        hex_data = " ".join(f"{b:02X}" for b in self.data)
        return f"Tag(tag={self.tag.tag_hex_str}, desc={self.tag.description}, len={len(self.data)}, data=[{hex_data}])"

@dataclass
class ParsedPacket:
    """
    Модель данных распарсенного пакета.
    """
    tags: List[ParsedTag]
    skipped_bytes: List[int] # Байты, которые не удалось распознать как теги (например, заголовок)
