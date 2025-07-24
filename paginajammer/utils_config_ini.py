import configparser
import os

# ------------- CONFIGURACIÓN DE RUTA -------------
# Ruta por defecto (pensada para tu Windows local)
DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "config.ini"
)

# Puedes forzarla con variable de entorno
CONFIG_PATH = os.environ.get("JAMMER_CONFIG_PATH", DEFAULT_CONFIG_PATH)


# ------------- FUNCIONES -------------------------

def leer_config(config_path=CONFIG_PATH):
    """
    Lee todos los parámetros del archivo config.ini.
    Devuelve un diccionario con los pares clave/valor.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Archivo no encontrado: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path)
    params = {}

    if "PARAMETROS" in config:
        for key in config["PARAMETROS"]:
            params[key] = config["PARAMETROS"][key]

    return params


def escribir_selector(valor, config_path=CONFIG_PATH):
    """
    Actualiza el valor de 'selector' en el config.ini.
    Valor esperado: 0 (apagado) o 1 (encendido).
    """
    config = configparser.ConfigParser()
    config.read(config_path)

    if "PARAMETROS" not in config:
        config["PARAMETROS"] = {}

    config["PARAMETROS"]["selector"] = str(valor)

    with open(config_path, "w") as configfile:
        config.write(configfile)


def actualizar_frecuencia(valor, config_path=CONFIG_PATH):
    """
    Actualiza la frecuencia en el config.ini.
    """
    config = configparser.ConfigParser()
    config.read(config_path)

    if "PARAMETROS" not in config:
        config["PARAMETROS"] = {}

    config["PARAMETROS"]["frecuencia"] = str(valor)

    with open(config_path, "w") as configfile:
        config.write(configfile)

# === FUNCIONES PARA COMPATIBILIDAD CON SISTEMA DE ALERTAS ===

def leer_valor(seccion, clave):
    params = leer_config()
    return params.get(clave)

def guardar_valor(seccion, clave, valor):
    if clave == "frecuencia":
        actualizar_frecuencia(valor)
    elif clave == "selector":
        escribir_selector(valor)
    else:
        raise ValueError(f"Parámetro no reconocido: {clave}")
