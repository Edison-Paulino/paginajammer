# paginajammer/monitor/launch_monitor.py
import threading
import time
from .monitoreo_alertas import (
    verificar_jammer_activo,
    verificar_temperatura_cpu,
)

def ciclo_alertas():
    while True:
        verificar_jammer_activo()
        verificar_temperatura_cpu()
        time.sleep(60)  # cada 60 segundos

def iniciar_monitor():
    t = threading.Thread(target=ciclo_alertas, daemon=True)
    t.start()


