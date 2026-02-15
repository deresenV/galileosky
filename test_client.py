import asyncio
import struct

async def send_test_packet():
    host = '127.0.0.1'
    port = 8080
    
    # Пример пакета из template.txt (первые N байт для теста)
    # Header (0x01) + Length (2 bytes) + Data + CRC (2 bytes)
    # Data from template: 01 90 90 ...
    # 01 - Header
    # 90 90 - Length (0x9090 & 0x7FFF = 0x1090 = 4240 bytes). 
    # В примере данные длинные, возьмем короткий кусок для теста.
    
    # Сформируем свой пакет с несколькими тегами
    # Tag 0x10 (Packet num): 0x10 (tag) + 0x10 (byte num) + 0x02 (len) + 0x00 0x01 (val=1) -> No, structure is just Tag + Data? 
    # Parser logic: Tag byte -> Tag object -> Length -> Read Data.
    # So stream: [TagByte] [Data...] [TagByte] [Data...]
    
    # Packet:
    # 0x01 (Head)
    # Len (2 bytes, LE)
    # Tags data...
    # CRC (2 bytes, LE)
    
    tags_payload = b''
    
    # Tag 0x10 (Num, 2 bytes): Val=1234 (0x04D2 -> D2 04)
    tags_payload += b'\x10\xD2\x04'
    
    # Tag 0x20 (Time, 4 bytes): Val=1700000000 (0x6554C100 -> 00 C1 54 65)
    tags_payload += b'\x20\x00\xC1\x54\x65'
    
    # Tag 0x30 (Coords, 9 bytes): 
    # Sats=10 (0x0A), Correct=1 (valid). Byte 0 = (Valid<<4 | Sats) = (1<<4 | 10) = 16|10 = 26 = 0x1A
    # Lat=55.7558 * 1000000 = 55755800 = 0x0352B418 -> 18 B4 52 03
    # Lon=37.6173 * 1000000 = 37617300 = 0x023DF694 -> 94 F6 3D 02
    tags_payload += b'\x30\x1A\x18\xB4\x52\x03\x94\xF6\x3D\x02'
    
    length = len(tags_payload)
    len_field = length | 0x8000 # Bit 15 is usually set for server packets? Or client?
    # Spec: "Bit 15 is 0 for client->server, 1 for server->client"? 
    # Or just length. Let's use simple length.
    len_field = length
    
    packet = b'\x01' + struct.pack('<H', len_field) + tags_payload
    
    # Calculate CRC (Simple CRC16 Modbus for test, or just dummy if server accepts anything? 
    # Server calculates received_crc from last 2 bytes. It doesn't validate it against data in this adapter version!
    # Wait, adapter extracts packet_data and sends back packet_data[-2:].
    # It does NOT validate CRC currently (PacketParser was used in original listener, here we use TagParser directly on tags_data).
    # We should append dummy CRC.
    packet += b'\xAA\xBB' 
    
    print(f"Sending {len(packet)} bytes to {host}:{port}...")
    
    try:
        reader, writer = await asyncio.open_connection(host, port)
        
        writer.write(packet)
        await writer.drain()
        
        # Read confirmation
        response = await reader.read(1024)
        print(f"Received response: {response.hex()}")
        
        writer.close()
        await writer.wait_closed()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_packet())
