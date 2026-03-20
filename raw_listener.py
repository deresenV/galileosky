import asyncio
import logging
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RawData:
    timestamp: datetime
    payload: bytes


class RawDataLogger(ABC):
    @abstractmethod
    async def log(self, data: RawData) -> None:
        pass


class FileRawDataLogger(RawDataLogger):
    def __init__(self, file_path: str):
        self._file_path = Path(file_path)
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    async def log(self, data: RawData) -> None:
        with open(self._file_path, "a", encoding="utf-8") as file:
            timestamp_str = data.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
            hex_payload = data.payload.hex().upper()
            file.write(f"{timestamp_str} - {hex_payload}\n")


class RawDataHandler:
    def __init__(self, logger: RawDataLogger):
        self._logger = logger

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer_name = writer.get_extra_info('peername')
        logging.info(f"Connected: {peer_name}")
        
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                
                raw_data = RawData(
                    timestamp=datetime.now(),
                    payload=data
                )
                await self._logger.log(raw_data)
                
        except asyncio.CancelledError:
            pass
        except Exception as error:
            logging.error(f"Error with {peer_name}: {error}")
        finally:
            writer.close()
            await writer.wait_closed()
            logging.info(f"Disconnected: {peer_name}")


class AsyncTcpServer:
    def __init__(self, host: str, port: int, handler: RawDataHandler):
        self._host = host
        self._port = port
        self._handler = handler

    async def start(self) -> None:
        server = await asyncio.start_server(
            self._handler.handle,
            self._host,
            self._port
        )
        
        addresses = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        logging.info(f"Server started on {addresses}")

        async with server:
            await server.serve_forever()


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = FileRawDataLogger("raw_listener.log")
    handler = RawDataHandler(logger)
    server = AsyncTcpServer("0.0.0.0", 12347, handler)
    
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server stopped manually")
