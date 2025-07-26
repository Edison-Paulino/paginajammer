import sqlite3
import os

PROJECT_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_BASE, 'db.sqlite3')


# ------------------------------
# Función: obtener_conexion
# ------------------------------
def obtener_conexion():
    return sqlite3.connect(DB_PATH)



# ------------------------------
# Función: insertar_registro
# ------------------------------
def insertar_registro(usuario, frecuencia_mhz, ubicacion, inicio_registro):
    """
    Inserta un nuevo registro de uso del jammer.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    sql = """
        INSERT INTO registros_jammer
        (usuario, frecuencia_mhz, ubicacion, inicio_registro)
        VALUES (?, ?, ?, ?)
    """
    cursor.execute(sql, (usuario, frecuencia_mhz, ubicacion, inicio_registro))
    conn.commit()
    conn.close()



# ------------------------------
# Función: cerrar_registro_abierto
# ------------------------------
def cerrar_registro_abierto(usuario, fin_registro):
    """
    Actualiza el registro abierto (sin fin_registro) para el usuario.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    sql = """
        UPDATE registros_jammer
        SET fin_registro = ?
        WHERE usuario = ? AND fin_registro IS NULL
    """
    cursor.execute(sql, (fin_registro, usuario))
    conn.commit()
    conn.close()



# ------------------------------
# Función: obtener_registro_abierto
# ------------------------------
def obtener_registro_abierto(usuario):
    """
    Obtiene el último registro abierto (sin fin_registro) del usuario.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    sql = """
        SELECT id, usuario, frecuencia_mhz, ubicacion, inicio_registro
        FROM registros_jammer
        WHERE usuario = ? AND fin_registro IS NULL
        ORDER BY inicio_registro DESC
        LIMIT 1
    """
    cursor.execute(sql, (usuario,))
    result = cursor.fetchone()
    conn.close()
    return result
