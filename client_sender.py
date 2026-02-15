import asyncio
import logging
from src.config import config

async def send_data():
    host = config.HOST
    port = config.PORT
    
    print(f"Connecting to {host}:{port}...")
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print("Connected!")
        
        # Читаем данные из template.txt
        with open("template.txt", "r") as f:
            hex_data = f.read().strip()
            
        binary_data = bytes.fromhex(hex_data)
        print(f"Sending {len(binary_data)} bytes...")
        
        writer.write(binary_data)
        await writer.drain()
        print("Data sent.")
        
        # Ждем подтверждения
        response = await reader.read(1024)
        print(f"Received response: {response.hex()}")
        
        writer.close()
        await writer.wait_closed()
        print("Connection closed.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_data())
