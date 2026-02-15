import asyncio
import logging
import struct
from typing import Dict, Any, Optional
from src.domain.parser import TagParser
from src.domain.decoders import TagDecoder
from src.domain.models import ParsedPacket
from src.config import config
from src.infrastructure.storage import JsonFileStorage

logger = logging.getLogger(__name__)

class GalileoskyListenerAdapter:
    """
    Адаптер для приема подключений от терминалов Galileosky и передачи данных в парсер.
    Интегрирует логику сетевого взаимодействия и бизнес-логику парсинга.
    """

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.server: Optional[asyncio.AbstractServer] = None
        self.storage = JsonFileStorage() # Инициализация хранилища

    async def start(self):
        """Запуск TCP сервера."""
        self.server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        addr = self.server.sockets[0].getsockname()
        logger.info(f"Galileosky Listener started on {addr}")
        logger.info(f"Data will be saved to {self.storage.file_path}")
        
        async with self.server:
            await self.server.serve_forever()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Обработка подключения клиента."""
        addr = writer.get_extra_info('peername')
        logger.info(f"New connection from {addr}")
        
        buffer = b''
        
        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(reader.read(1024), timeout=config.TIMEOUT)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout from {addr}")
                    break
                    
                if not chunk:
                    break
                
                buffer += chunk
                
                # Обработка буфера
                while len(buffer) > 3: # Min size: Header(1) + Len(2)
                    if buffer[0] != 0x01:
                        logger.warning(f"Garbage data detected from {addr}, skipping byte {hex(buffer[0])}")
                        buffer = buffer[1:]
                        continue
                        
                    # Парсинг длины (Little Endian)
                    len_field = struct.unpack('<H', buffer[1:3])[0]
                    length = len_field & 0x7FFF
                    
                    expected_len = 1 + 2 + length + 2 # Header + Len + Data + CRC
                    
                    if len(buffer) < expected_len:
                        break
                        
                    # Извлечение пакета
                    packet_data = buffer[:expected_len]
                    # Данные тегов (без заголовка, длины и CRC)
                    tags_data = packet_data[3:-2] 
                    buffer = buffer[expected_len:]
                    
                    try:
                        # 1. Парсинг структуры тегов
                        # TagParser ожидает List[int], преобразуем bytes -> list
                        byte_list = list(tags_data)
                        parser = TagParser()
                        parsed_packet: ParsedPacket = parser.parse(byte_list)
                        
                        await self.process_parsed_data(addr, parsed_packet)
                        
                        # 2. Отправка подтверждения
                        received_crc = struct.unpack('<H', packet_data[-2:])[0]
                        response = b'\x02' + struct.pack('<H', received_crc)
                        
                        writer.write(response)
                        await writer.drain()
                        logger.debug(f"Sent confirmation to {addr}")
                        
                    except Exception as e:
                        logger.error(f"Error processing packet from {addr}: {e}", exc_info=True)
                        
        except Exception as e:
            logger.error(f"Connection error with {addr}: {e}")
        finally:
            logger.info(f"Connection closed {addr}")
            writer.close()
            await writer.wait_closed()

    async def process_parsed_data(self, addr, packet: ParsedPacket):
        """
        Обработка распарсенных данных (декодирование и логирование/сохранение).
        """
        logger.info(f"Received packet from {addr} with {len(packet.tags)} tags")
        
        packet_dict = {
            "source_ip": addr[0],
            "source_port": addr[1],
            "tags": {}
        }
        
        for tag in packet.tags:
            try:
                decoded_value = TagDecoder.decode(tag.tag.num, tag.data)
                tag_key = tag.tag.tag_hex_str # e.g. "0x10"
                packet_dict["tags"][tag_key] = decoded_value
                
                if config.DEBUG:
                    logger.debug(f"  Tag {tag.tag.tag_hex_str}: {decoded_value}")

            except Exception as e:
                logger.error(f"Failed to decode tag {tag.tag.tag_hex_str}: {e}")
                
        # Сохранение в хранилище
        await self.storage.save(packet_dict)
