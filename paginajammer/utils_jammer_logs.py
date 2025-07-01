import os

# Carpeta estándar en Raspberry Pi
DEFAULT_LOG_DIR = "/var/log/jammer_logs/"

# Para desarrollo local (puedes simular la carpeta)
LOCAL_LOG_DIR = os.path.dirname(__file__)

# Decide ruta en función de entorno
LOG_DIR = os.environ.get("JAMMER_LOG_DIR", LOCAL_LOG_DIR)

JAMMER_STATE_PATH = os.path.join(LOG_DIR, "jammer_state.flag")
UNEXPECTED_LOG_PATH = os.path.join(LOG_DIR, "unexpected_shutdown.log")


def leer_estado_actual():
    """
    Lee el archivo jammer_state.flag y devuelve un dict con:
    - timestamp
    - selector
    """
    if not os.path.exists(JAMMER_STATE_PATH):
        print(f"[WARN] No existe: {JAMMER_STATE_PATH}")
        return None

    data = {}
    with open(JAMMER_STATE_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip()
    return data


def leer_historial_apagados():
    """
    Lee el archivo unexpected_shutdown.log y devuelve lista de líneas (historial).
    """
    if not os.path.exists(UNEXPECTED_LOG_PATH):
        print(f"[WARN] No existe: {UNEXPECTED_LOG_PATH}")
        return []

    with open(UNEXPECTED_LOG_PATH, "r") as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.strip()]
