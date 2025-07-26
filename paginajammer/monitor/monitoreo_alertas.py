
from datetime import datetime, timedelta
from paginajammer.utils_alertas_db import crear_alerta
from paginajammer.utils_config_ini import leer_valor, guardar_valor
from usuarios.models import RegistroJammer

    
# === Alerta: Jammer activo prolongado ===
def verificar_jammer_activo():
    try:
        estado = leer_valor('sistema', 'estado')
        if estado == '1':
            with open("jammer_state.flag", "r") as f:
                timestamp = float(f.read().strip())
            duracion = (datetime.now().timestamp() - timestamp) / 60
            if duracion > 300:
                crear_alerta(
                    nombre="Jammer activo prolongado",
                    descripcion="El jammer ha estado encendido más de 5 horas.",
                    nivel="WARN",
                    codigo="JAMMER_ON"
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
                codigo="CPU_HIGH_TEMP"
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
            codigo="CONFIG_FAIL"
        )

# === Alerta: Restauración de CONFIG segura ===
def restaurar_valores_seguro():
    crear_alerta(
        nombre="Restauración de CONFIG segura",
        descripcion="Se restauraron valores seguros en CONFIG.INI tras detectar errores.",
        nivel="INFO",
        codigo="SAFE_RESTORE"
    )

# === Alerta: WebSocket caída ===
def registrar_websocket_desconexion(close_code):
    crear_alerta(
        nombre="Caída de WebSocket",
        descripcion=f"WebSocket desconectado con código {close_code}.",
        nivel="INFO",
        codigo="WS_DISCONNECT"
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
            codigo="WS_RECONNECT"
        )

# === Alerta: Intento de acceso no autorizado ===
def registrar_intento_no_autorizado(ip):
    crear_alerta(
        nombre="Intento de acceso no autorizado",
        descripcion=f"Intento de acceso sin permisos desde IP {ip}",
        nivel="ERROR",
        codigo="UNAUTHORIZED"
    )

# === Alerta: Pico fuerte en banda crítica ===
def detectar_pico_frecuencia(frecuencia_detectada, amplitud_dbm):
    if 2400 <= frecuencia_detectada <= 2483.5 and amplitud_dbm > -40:
        crear_alerta(
            nombre="Pico fuerte en banda crítica",
            descripcion=f"Se detectó un pico de {amplitud_dbm} dBm en {frecuencia_detectada} MHz.",
            nivel="WARN",
            codigo="BANDA_CRITICA"
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
                codigo="INTERFERENCIA"
            )
            interferencia_tiempo = None
    else:
        interferencia_tiempo = None

def verificar_registros_consecutivos():
    registros = RegistroJammer.objects.all().order_by('inicio_registro')
    sesiones = []
    sesion_actual = []

    for r in registros:
        inicio = r.inicio_registro
        fin = r.fin_registro or datetime.now()

        if not sesion_actual:
            sesion_actual.append((inicio, fin))
        else:
            _, fin_anterior = sesion_actual[-1]
            if (inicio - fin_anterior) <= timedelta(minutes=30):
                sesion_actual.append((inicio, fin))
            else:
                sesiones.append(sesion_actual)
                sesion_actual = [(inicio, fin)]

    if sesion_actual:
        sesiones.append(sesion_actual)

    for grupo in sesiones:
        duracion_total = sum([(fin - inicio).total_seconds() for inicio, fin in grupo]) / 60  # en minutos
        if duracion_total >= 300:
            crear_alerta(
                nombre="Actividad prolongada con interrupciones breves",
                descripcion="Se detectó una secuencia de registros de jammer consecutivos que acumulan más de 5 horas.",
                nivel="CRITICAL",
                codigo="JAMMER_MULTI_ON"
            )
            break  # Solo una alerta por ejecución


if __name__ == "__main__":
    from paginajammer.utils_alertas_db import crear_alerta
    crear_alerta(
        nombre="Alerta de prueba",
        descripcion="Esta es una alerta generada manualmente",
        nivel="INFO",
        codigo="TEST_ALERT"
    )


