import sqlite3
import os
from datetime import datetime

PROJECT_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_BASE, 'db.sqlite3')



# ------------------------------
# Función: obtener_conexion
# ------------------------------
def obtener_conexion():
    return sqlite3.connect(DB_PATH)


# ------------------------------
# Función: insertar_alerta
# ------------------------------
def insertar_alerta(titulo, descripcion, nivel, usuario=None):
    """
    Inserta una nueva alerta en la base de datos.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    sql = """
        INSERT INTO alertas (titulo, descripcion, nivel, fecha_hora, usuario)
        VALUES (?, ?, ?, ?, ?)
    """
    now = datetime.now().isoformat()
    cursor.execute(sql, (titulo, descripcion, nivel, now, usuario))
    conn.commit()
    conn.close()


from datetime import datetime


# ------------------------------
# Función: formatear_fecha
# ------------------------------
def formatear_fecha(fecha_str):
    try:
        dt = datetime.fromisoformat(fecha_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return fecha_str


# ------------------------------
# Función: obtener_todas_alertas
# ------------------------------
def obtener_todas_alertas():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM alertas")
    datos = cursor.fetchall()
    conexion.close()

    alertas = []
    for a in datos:
        alerta = list(a)
        alerta[4] = formatear_fecha(alerta[4])
        alertas.append(alerta)

    return alertas




# ------------------------------
# Función: existe_alerta_descripcion
# ------------------------------
def existe_alerta_descripcion(descripcion):
    conn = obtener_conexion()
    cursor = conn.cursor()
    sql = "SELECT COUNT(*) FROM alertas WHERE descripcion = ?"
    cursor.execute(sql, (descripcion,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


from usuarios.models import Alerta


# ------------------------------
# Función: crear_alerta
# ------------------------------
def crear_alerta(nombre, descripcion, nivel, codigo):
    try:
        alerta = Alerta.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            nivel=nivel,
            codigo=codigo
        )
        print(f"✅ Alerta creada: {alerta}")
        return True
    except Exception as e:
        print(f"❌ Error al crear alerta: {e}")
        return False
