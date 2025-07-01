import sqlite3
import os

# Ruta a db.sqlite3 en tu proyecto Django local
PROJECT_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_BASE, 'db.sqlite3')


def obtener_conexion():
    """
    Devuelve una conexión a la base de datos SQLite local.
    """
    return sqlite3.connect(DB_PATH)


def insertar_registro(usuario_inicio, frecuencia_mhz, ubicacion, inicio_registro):
    """
    Inserta un nuevo registro de uso del jammer.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    sql = """
        INSERT INTO registros_jammer
        (usuario_inicio, frecuencia_mhz, ubicacion, inicio_registro)
        VALUES (?, ?, ?, ?)
    """
    cursor.execute(sql, (usuario_inicio, frecuencia_mhz, ubicacion, inicio_registro))
    conn.commit()
    conn.close()


def cerrar_registro_abierto(usuario_fin, fin_registro):
    """
    Cierra todos los registros abiertos de este usuario (con usuario_inicio = usuario).
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    sql = """
        UPDATE registros_jammer
        SET fin_registro = ?, usuario_fin = ?
        WHERE usuario_fin IS NULL AND fin_registro IS NULL
    """
    cursor.execute(sql, (fin_registro, usuario_fin))
    conn.commit()
    conn.close()


def cerrar_todos_registros_abiertos(usuario_fin, fin_registro):
    """
    Cierra TODOS los registros abiertos de cualquier usuario.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    sql = """
        UPDATE registros_jammer
        SET fin_registro = ?, usuario_fin = ?
        WHERE usuario_fin IS NULL AND fin_registro IS NULL
    """
    cursor.execute(sql, (fin_registro, usuario_fin))
    conn.commit()
    conn.close()


def obtener_registro_abierto_usuario(usuario_inicio):
    """
    Obtiene el último registro abierto (sin fin_registro) del usuario específico.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    sql = """
        SELECT id, usuario_inicio, frecuencia_mhz, ubicacion, inicio_registro
        FROM registros_jammer
        WHERE usuario_inicio = ? AND fin_registro IS NULL
        ORDER BY inicio_registro DESC
        LIMIT 1
    """
    cursor.execute(sql, (usuario_inicio,))
    result = cursor.fetchone()
    conn.close()
    return result


def obtener_cualquier_registro_abierto():
    """
    Devuelve el primer registro abierto (fin_registro IS NULL) de cualquier usuario.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    sql = """
        SELECT id, usuario_inicio, frecuencia_mhz, ubicacion, inicio_registro
        FROM registros_jammer
        WHERE fin_registro IS NULL
        ORDER BY inicio_registro ASC
        LIMIT 1
    """
    cursor.execute(sql)
    result = cursor.fetchone()
    conn.close()
    return result


def obtener_todos_registros():
    """
    Devuelve todos los registros de uso del jammer.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    sql = """
        SELECT id, usuario_inicio, usuario_fin, frecuencia_mhz, ubicacion, inicio_registro, fin_registro
        FROM registros_jammer
        ORDER BY inicio_registro DESC
    """
    cursor.execute(sql)
    results = cursor.fetchall()
    conn.close()
    return results


def obtener_registros_por_usuario(usuario_inicio):
    """
    Devuelve todos los registros iniciados por un usuario específico.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    sql = """
        SELECT id, usuario_inicio, usuario_fin, frecuencia_mhz, ubicacion, inicio_registro, fin_registro
        FROM registros_jammer
        WHERE usuario_inicio = ?
        ORDER BY inicio_registro DESC
    """
    cursor.execute(sql, (usuario_inicio,))
    results = cursor.fetchall()
    conn.close()
    return results
