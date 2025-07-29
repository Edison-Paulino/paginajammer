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

        # Leer CONFIG.INI una vez al inicio
        self.center_freq = self.get_center_freq()
        self.samp_rate = 28e6  # Constante

        # Inicializar ZMQ
        self.zmq_context = zmq.asyncio.Context()
        self.zmq_socket = self.zmq_context.socket(zmq.SUB)
        self.zmq_socket.connect("tcp://127.0.0.1:5678")
        self.zmq_socket.setsockopt(zmq.SUBSCRIBE, b"")

        # Lanzar tarea de escucha
        self.fft_task = asyncio.create_task(self.receive_fft())

        # Tarea secundaria para refrescar frecuencia cada 5s
        self.config_task = asyncio.create_task(self.config_monitor_loop())

    async def disconnect(self, close_code):
        self.running = False
        self.fft_task.cancel()
        self.config_task.cancel()
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

    async def config_monitor_loop(self):
        while self.running:
            try:
                self.center_freq = self.get_center_freq()
            except Exception as e:
                print("Error leyendo CONFIG.INI:", e)
            await asyncio.sleep(5)

    def get_center_freq(self):
        config = configparser.ConfigParser()
        config.read('D:/django_project/paginajammer/paginajammer/CONFIG.INI')
        return float(config['PARAMETROS']['frecuencia'])

    # 🔄 MODIFICAR receive_fft PARA OMITIR OFFSET Y USAR TODO EL VECTOR COMPLETO
    async def receive_fft(self):
        fft_size = 8192

        while self.running:
            try:
                if self.zmq_socket.poll(timeout=1000):
                    msg = await self.zmq_socket.recv()
                else:
                    continue

                raw_data = list(memoryview(msg).cast('f'))

                if len(raw_data) != fft_size:
                    print("⚠️ Tamaño inesperado de FFT:", len(raw_data))
                    continue

                await self.send(json.dumps({
                    "type": "fft",
                    "values": raw_data,
                    "center_freq": self.center_freq,
                    "samp_rate": self.samp_rate,
                    "fft_size": fft_size
                }))

            except asyncio.CancelledError:
                break

            except Exception as e:
                print("ZMQ error:", e)
                await self.send(json.dumps({"type": "error", "detail": str(e)}))
                await asyncio.sleep(1)
