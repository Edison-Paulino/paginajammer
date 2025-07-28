import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from usuarios.routing import websocket_urlpatterns
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paginajammer.settings')
django.setup()

import paginajammer.asgi_startup

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )   
    ),
})

import subprocess
import threading
import os
import psutil  # Asegúrate de instalarlo con: pip install psutil
import time


def script_ya_ejecutado(nombre_script):
    """Verifica si ya hay un proceso corriendo con el nombre del script."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline and any(nombre_script.lower() in os.path.basename(arg).lower() for arg in cmdline):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False



def ejecutar_gnu_radio():
    print("🚀 [ASGI] Forzando ejecución del script Jammer...")

    ruta_script = os.path.join(os.path.dirname(__file__), 'monitor', 'JammerP2_NoGui.py')
    path_python_radioconda = r"C:\Users\ediso\radioconda\python.exe"  # Ajusta si cambia

    while True:
        try:
            proceso = subprocess.Popen([path_python_radioconda, ruta_script])
            print("✅ [ASGI] Script lanzado forzadamente.")
            proceso.wait()  # Espera a que el script termine (ya sea por error o cierre)
            print("⚠️ [ASGI] El script terminó. Reiniciando en 3 segundos...")
            time.sleep(3)
        except Exception as e:
            print(f"❌ [ASGI] Error al ejecutar el script: {e}")
            time.sleep(5)

# Ejecutar en hilo separado
threading.Thread(target=ejecutar_gnu_radio, daemon=True).start()
