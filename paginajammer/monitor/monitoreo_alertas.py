
from datetime import datetime, timedelta
from paginajammer.utils_alertas_db import crear_alerta
from paginajammer.utils_config_ini import leer_valor, guardar_valor

# === Alerta: Jammer activo prolongado ===
def verificar_jammer_activo():
    try:
        estado = leer_valor('sistema', 'estado')
        if estado == '1':
            with open("jammer_state.flag", "r") as f:
                timestamp = float(f.read().strip())
            duracion = (datetime.now().timestamp() - timestamp) / 60
            if duracion > 10:
                crear_alerta(
                    nombre="Jammer activo prolongado",
                    descripcion="El jammer ha estado encendido más de 10 minutos.",
                    nivel="WARN",
                    codigo="A002"
                )
    except Exception as e:
        print("Error verificando jammer:", e)

# === Alerta: CPU sobrecalentada ===
def verificar_temperatura_cpu():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            temp_c = int(f.read()) / 1000
        if temp_c > 75:
            crear_alerta(
                nombre="CPU sobrecalentada",
                descripcion=f"Temperatura crítica detectada: {temp_c:.1f} °C.",
                nivel="ERROR",
                codigo="A004"
            )
    except Exception as e:
        print("No se pudo leer temperatura CPU:", e)

# === Alerta: Error escribiendo CONFIG.INI ===
def guardar_valor_con_alerta(seccion, clave, valor):
    try:
        guardar_valor(seccion, clave, valor)
    except Exception as e:
        crear_alerta(
            nombre="Error escribiendo CONFIG.INI",
            descripcion=f"No se pudo guardar el parámetro '{clave}': {e}",
            nivel="ERROR",
            codigo="A006"
        )

# === Alerta: Restauración de CONFIG segura ===
def restaurar_valores_seguro():
    crear_alerta(
        nombre="Restauración de CONFIG segura",
        descripcion="Se restauraron valores seguros en CONFIG.INI tras detectar errores.",
        nivel="INFO",
        codigo="A008"
    )

# === Alerta: WebSocket caída ===
def registrar_websocket_desconexion(close_code):
    crear_alerta(
        nombre="Caída de WebSocket",
        descripcion=f"WebSocket desconectado con código {close_code}.",
        nivel="INFO",
        codigo="C002"
    )

# === Alerta: Reconexión WebSocket frecuente ===
conexion_logs = []

def registrar_conexion_websocket():
    ahora = datetime.now()
    conexion_logs.append(ahora)
    conexion_logs[:] = [t for t in conexion_logs if ahora - t < timedelta(minutes=2)]
    if len(conexion_logs) >= 3:
        crear_alerta(
            nombre="Reconexión WebSocket frecuente",
            descripcion="Más de 3 reconexiones de WebSocket en menos de 2 minutos.",
            nivel="INFO",
            codigo="C004"
        )

# === Alerta: Intento de acceso no autorizado ===
def registrar_intento_no_autorizado(ip):
    crear_alerta(
        nombre="Intento de acceso no autorizado",
        descripcion=f"Intento de acceso sin permisos desde IP {ip}",
        nivel="ERROR",
        codigo="S001"
    )

# === Alerta: Pico fuerte en banda crítica ===
def detectar_pico_frecuencia(frecuencia_detectada, amplitud_dbm):
    if 2400 <= frecuencia_detectada <= 2483.5 and amplitud_dbm > -40:
        crear_alerta(
            nombre="Pico fuerte en banda crítica",
            descripcion=f"Se detectó un pico de {amplitud_dbm} dBm en {frecuencia_detectada} MHz.",
            nivel="WARN",
            codigo="F001"
        )

# === Alerta: Interferencia sostenida ===
interferencia_tiempo = None

def detectar_interferencia_continua(potencia_dbm):
    global interferencia_tiempo
    ahora = datetime.now()

    if potencia_dbm > -50:
        if not interferencia_tiempo:
            interferencia_tiempo = ahora
        elif (ahora - interferencia_tiempo).total_seconds() > 10:
            crear_alerta(
                nombre="Interferencia sostenida",
                descripcion="Se mantiene una señal fuerte en el espectro por más de 10 segundos.",
                nivel="WARN",
                codigo="F002"
            )
            interferencia_tiempo = None
    else:
        interferencia_tiempo = None


if __name__ == "__main__":
    from paginajammer.utils_alertas_db import crear_alerta
    crear_alerta(
        nombre="Alerta de prueba",
        descripcion="Esta es una alerta generada manualmente",
        nivel="INFO",
        codigo="T001"
    )
