import json
import asyncio
import zmq
import zmq.asyncio
import configparser
from channels.generic.websocket import AsyncWebsocketConsumer

class MonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.running = True
        self.zmq_context = zmq.asyncio.Context()
        self.zmq_socket = self.zmq_context.socket(zmq.SUB)
        self.zmq_socket.connect("tcp://127.0.0.1:5678")
        self.zmq_socket.setsockopt(zmq.SUBSCRIBE, b"")
        self.fft_task = asyncio.create_task(self.receive_fft())

    async def disconnect(self, close_code):
        self.running = False
        self.fft_task.cancel()
        try:
            self.zmq_socket.close()
            self.zmq_context.term()
        except Exception as e:
            print("Error al cerrar ZMQ:", e)

    async def receive(self, text_data):
        try:
            msg = json.loads(text_data)
            if msg.get("type") == "ping":
                return
        except:
            pass

    async def receive_fft(self):
        samp_rate = 28e6
        fft_size = 8192
        while self.running:
            try:
                # Leer frecuencia desde .ini
                config = configparser.ConfigParser()
                config.read('D:/django_project/paginajammer/paginajammer/CONFIG.INI')
                center_freq = float(config['PARAMETROS']['frecuency'])

                msg = await self.zmq_socket.recv()
                raw_data = list(memoryview(msg).cast('f'))

                # Recortar para asegurar tamaño válido
                data = raw_data[:fft_size]

                #print("Tamaño de data:", len(data))
                #print("Datos enviados:", data[:10])



                # Verifica que aún el WebSocket esté abierto
                if not self.running:
                    break

                await self.send(json.dumps({
                    "type": "fft",
                    "values": data,
                    "center_freq": center_freq,
                    "samp_rate": samp_rate,
                    "fft_size": fft_size
                }))

            except asyncio.CancelledError:
                break

            except Exception as e:
                print("ZMQ error:", e)
                await asyncio.sleep(0.5)
