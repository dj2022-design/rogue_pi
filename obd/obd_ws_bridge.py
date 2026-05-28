#!/usr/bin/env python3
import obd
import time
import json
import asyncio
import websockets

OBD_PORT  = '/dev/rfcomm0'
WS_PORT   = 8765
HTTP_PORT = 8766
INTERVAL  = 1.0
RETRY     = 5.0

COMMANDS = {
    'speed':        obd.commands.SPEED,
    'rpm':          obd.commands.RPM,
    'coolant_temp': obd.commands.COOLANT_TEMP,
    'engine_load':  obd.commands.ENGINE_LOAD,
    'fuel_level':   obd.commands.FUEL_LEVEL,
    'intake_temp':  obd.commands.INTAKE_TEMP,
    'voltage':      obd.commands.ELM_VOLTAGE,
}

conn = None
dtc_cache = {'codes': [], 'scanned_at': ''}
clients = set()

def obd_connect_sync():
    global conn
    while True:
        try:
            print(f'Connecting to {OBD_PORT}...')
            c = obd.OBD(OBD_PORT)
            if str(c.status()) == 'Car Connected':
                conn = c
                print('OBD connected!')
                return
            print(f'Status: {c.status()}, retrying...')
        except Exception as e:
            print(f'Connect error: {e}')
        time.sleep(RETRY)

def read_dtc_sync():
    global dtc_cache
    if not conn: return
    try:
        from obd import ECU
        obd.commands.GET_DTC.ecu = ECU.ALL
        r = conn.query(obd.commands.GET_DTC, force=True)
        codes = [str(c[0]) for c in r.value] if r.value else []
        dtc_cache = {'codes': codes, 'scanned_at': time.strftime('%H:%M')}
        print(f'DTC: {codes if codes else "clean"}')
    except Exception as e:
        print(f'DTC error: {e}')

def read_obd_sync():
    global conn
    if not conn:
        return {'connected': False}
    data = {'connected': True}
    fail = 0
    for key, cmd in COMMANDS.items():
        try:
            r = conn.query(cmd)
            data[key] = round(float(r.value.magnitude), 2) if not r.is_null() else None
        except:
            data[key] = None
            fail += 1
    if fail >= len(COMMANDS):
        print('All queries failed, reconnecting...')
        try: conn.close()
        except: pass
        conn = None
    return data

async def ws_handler(ws):
    global clients
    clients.add(ws)
    print(f'WS client connected, total: {len(clients)}')
    try:
        await ws.wait_closed()
    finally:
        clients.discard(ws)

async def broadcast_loop():
    global clients, conn
    while True:
        if not conn:
            await asyncio.to_thread(obd_connect_sync)
            await asyncio.to_thread(read_dtc_sync)
        data = await asyncio.to_thread(read_obd_sync)
        data['timestamp'] = time.time()
        msg = json.dumps(data)
        dead = set()
        for ws in clients.copy():
            try:
                await ws.send(msg)
            except:
                dead.add(ws)
        clients -= dead
        await asyncio.sleep(INTERVAL)

async def http_handler(reader, writer):
    await reader.read(1024)
    body = json.dumps(dtc_cache)
    resp = (
        'HTTP/1.1 200 OK\r\n'
        'Content-Type: application/json\r\n'
        'Access-Control-Allow-Origin: *\r\n'
        f'Content-Length: {len(body)}\r\n'
        '\r\n' + body
    )
    writer.write(resp.encode())
    await writer.drain()
    writer.close()

async def main():
    await asyncio.to_thread(obd_connect_sync)
    await asyncio.to_thread(read_dtc_sync)
    ws_server   = await websockets.serve(ws_handler, '0.0.0.0', WS_PORT)
    http_server = await asyncio.start_server(http_handler, '0.0.0.0', HTTP_PORT)
    print(f'WS :{WS_PORT}, HTTP :{HTTP_PORT}')
    await asyncio.gather(
        ws_server.serve_forever(),
        http_server.serve_forever(),
        broadcast_loop(),
    )

if __name__ == '__main__':
    asyncio.run(main())
