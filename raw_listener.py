import asyncio
import logging
import struct
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RawData:
    timestamp: datetime
    payload: bytes
    client_ip: str
    client_port: int


class RawDataLogger(ABC):
    @abstractmethod
    async def log(self, data: RawData) -> None:
        pass


class FileRawDataLogger(RawDataLogger):
    def __init__(self, file_path: str):
        self._file_path = Path(file_path)
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        logging.info(f"Initialized FileRawDataLogger with path: {self._file_path.absolute()}")

    async def log(self, data: RawData) -> None:
        logging.debug(f"Writing data to log file {self._file_path.name}...")
        with open(self._file_path, "a", encoding="utf-8") as file:
            timestamp_str = data.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
            hex_payload = data.payload.hex().upper()
            file.write(f"{timestamp_str} | {data.client_ip}:{data.client_port} | {hex_payload}\n")
        logging.debug(f"Data successfully written to {self._file_path.name}")


class RawDataHandler:
    def __init__(self, logger: RawDataLogger):
        self._logger = logger

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer_name = writer.get_extra_info('peername')
        client_ip, client_port = peer_name[0], peer_name[1]
        logging.info(f"New client connected: {client_ip}:{client_port}")
        
        buffer = b''
        
        try:
            while True:
                logging.debug(f"Waiting for data from {client_ip}:{client_port}...")
                chunk = await reader.read(1024)
                
                if not chunk:
                    logging.info(f"Client {client_ip}:{client_port} closed the connection")
                    break
                
                logging.debug(f"Received {len(chunk)} bytes from {client_ip}:{client_port}")
                buffer += chunk
                logging.debug(f"Current buffer size: {len(buffer)} bytes")
                
                while len(buffer) >= 3:
                    if buffer[0] != 0x01:
                        logging.warning(f"Invalid start byte detected: {hex(buffer[0])}. Discarding 1 byte.")
                        buffer = buffer[1:]
                        continue
                        
                    length_bytes = buffer[1:3]
                    length_field = struct.unpack('<H', length_bytes)[0]
                    payload_length = length_field & 0x7FFF
                    logging.debug(f"Parsed payload length: {payload_length} bytes")
                    
                    expected_total_length = 1 + 2 + payload_length + 2
                    logging.debug(f"Expected total packet length: {expected_total_length} bytes")
                    
                    if len(buffer) < expected_total_length:
                        logging.debug(f"Buffer too small ({len(buffer)} bytes). Waiting for more data...")
                        break
                        
                    packet_data = buffer[:expected_total_length]
                    
                    raw_data = RawData(
                        timestamp=datetime.now(),
                        payload=packet_data,
                        client_ip=client_ip,
                        client_port=client_port
                    )
                    
                    logging.debug(f"Delegating packet saving to logger...")
                    await self._logger.log(raw_data)
                    
                    buffer = buffer[expected_total_length:]
                    logging.info(f"Successfully extracted full packet of {expected_total_length} bytes from {client_ip}:{client_port}")
                    
                    crc_bytes = packet_data[-2:]
                    logging.debug(f"Extracted CRC: {crc_bytes.hex().upper()}")
                    
                    ack_response = b'\x02' + crc_bytes
                    logging.debug(f"Sending ACK: {ack_response.hex().upper()} to {client_ip}:{client_port}")
                    writer.write(ack_response)
                    await writer.drain()
                    logging.info(f"ACK successfully sent to {client_ip}:{client_port}")
                    
        except asyncio.CancelledError:
            logging.info(f"Connection task cancelled for {client_ip}:{client_port}")
        except Exception as error:
            logging.error(f"Unexpected error with {client_ip}:{client_port}: {error}", exc_info=True)
        finally:
            logging.debug(f"Closing connection writer for {client_ip}:{client_port}...")
            writer.close()
            await writer.wait_closed()
            logging.info(f"Connection fully closed and cleaned up for {client_ip}:{client_port}")


class AsyncTcpServer:
    def __init__(self, host: str, port: int, handler: RawDataHandler):
        self._host = host
        self._port = port
        self._handler = handler

    async def start(self) -> None:
        logging.info(f"Starting AsyncTcpServer on {self._host}:{self._port}...")
        server = await asyncio.start_server(
            self._handler.handle,
            self._host,
            self._port
        )
        
        addresses = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        logging.info(f"Server successfully bound and listening on {addresses}")

        async with server:
            logging.debug("Entering main server loop...")
            await server.serve_forever()


async def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
    )
    
    logging.info("Initializing raw listener application...")
    logger = FileRawDataLogger("raw_listener.log")
    handler = RawDataHandler(logger)
    server = AsyncTcpServer("0.0.0.0", 12347, handler)
    
    logging.info("Application initialization complete. Starting server.")
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server stopped manually via KeyboardInterrupt")