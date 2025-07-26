import sys
import os
from datetime import datetime, timedelta

# Establecer correctamente la ruta base del proyecto
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

# Configuración del entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paginajammer.settings')

import django
django.setup()

# Importar funciones del sistema de monitoreo
from paginajammer.monitor.monitoreo_alertas import (
    verificar_jammer_activo,
    verificar_temperatura_cpu,
    guardar_valor_con_alerta,
    restaurar_valores_seguro,
    registrar_websocket_desconexion,
    registrar_conexion_websocket,
    registrar_intento_no_autorizado,
    detectar_pico_frecuencia,
    detectar_interferencia_continua
)

from datetime import datetime

# Simula que el jammer está encendido desde hace más de 10 minutos
with open("jammer_state.flag", "w") as f:
    hace_15_min = datetime.now().timestamp() - (15 * 60)
    f.write(str(hace_15_min))

print("▶️ Simulando JAMMER_ON...")
verificar_jammer_activo()

print("▶️ Simulando CPU_HIGH_TEMP...")
verificar_temperatura_cpu()

print("▶️ Simulando CONFIG_FAIL...")
guardar_valor_con_alerta("sistema", "clave_invalida", object())  # valor no serializable

print("▶️ Simulando SAFE_RESTORE...")
restaurar_valores_seguro()

print("▶️ Simulando WS_DISCONNECT...")
registrar_websocket_desconexion(close_code=1006)

print("▶️ Simulando WS_RECONNECT...")
registrar_conexion_websocket()
registrar_conexion_websocket()
registrar_conexion_websocket()

print("▶️ Simulando UNAUTHORIZED...")
registrar_intento_no_autorizado("192.168.0.123")

print("▶️ Simulando BANDA_CRITICA...")
detectar_pico_frecuencia(frecuencia_detectada=2450, amplitud_dbm=-35)

print("▶️ Simulando INTERFERENCIA...")
for _ in range(12):
    detectar_interferencia_continua(potencia_dbm=-45)




from usuarios.models import RegistroJammer, User


def simular_registros_consecutivos():
    print("▶️ Simulando registros consecutivos para JAMMER_MULTI_ON...")

    # Usuarios de prueba (asegúrate de que existan)
    usuario1 = User.objects.get(username="epj01")
    usuario2 = User.objects.get(username="asm01")

    from django.utils import timezone
    now = timezone.now()


    # Crear 6 bloques de 50 minutos de duración con 20 minutos de pausa entre ellos (total ~5h)
    for i in range(6):
        inicio = now - timedelta(hours=6, minutes=-i * 70)
        fin = inicio + timedelta(minutes=50)
        user = usuario1 if i % 2 == 0 else usuario2
        RegistroJammer.objects.create(
            usuario_inicio=user,
            usuario_fin=user,
            frecuencia_mhz=2450.0,
            ubicacion="Prueba",
            inicio_registro=inicio,
            fin_registro=fin
        )

    print("✅ Registros simulados.")

simular_registros_consecutivos()




from paginajammer.monitor.monitoreo_alertas import verificar_registros_consecutivos

verificar_registros_consecutivos()


print("✅ Simulación completa.")