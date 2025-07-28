import os
import sys
import django
import random

# Configurar entorno Django
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paginajammer.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario

nombres = ["Juan", "Pedro", "Luis", "Carlos", "José", "Miguel", "Andrés", "Francisco", "Manuel", "Rafael"]
apellidos = ["Martínez", "Pérez", "Gómez", "Díaz", "Sánchez", "Ramírez", "Rodríguez", "Fernández", "Jiménez", "Morales"]
segundos_nombres = ["Antonio", "Eduardo", "Ricardo", "Elías", "Enrique", "Jesús", "Domingo", "David", "Alfredo", "Esteban"]
segundos_apellidos = ["Reyes", "Nova", "López", "Torres", "Ortiz", "Cruz", "Bautista", "Vásquez", "Castillo", "Mejía"]
prefijos_telefono = ["809", "829", "849"]

cantidad = 20
creados = 0

for i in range(cantidad):
    nombre = random.choice(nombres)
    segundo_nombre = random.choice(segundos_nombres)
    apellido = random.choice(apellidos)
    segundo_apellido = random.choice(segundos_apellidos)

    # username más variable para evitar colisiones
    username = f"{nombre[0].lower()}{apellido[0].lower()}{segundo_apellido[0].lower()}{"01"}"

    # Si ya existe, lo salta
    if User.objects.filter(username=username).exists():
        continue

    email = f"{username}@gmail.com"
    telefono = f"{random.choice(prefijos_telefono)}{random.randint(2000000, 9999999)}"

    user = User.objects.create_user(
        username=username,
        email=email,
        password="12345678",
        first_name=nombre,
        last_name=apellido
    )

    # Crear o actualizar perfil asociado
    perfil, creado = PerfilUsuario.objects.get_or_create(user=user)
    perfil.segundo_nombre = segundo_nombre
    perfil.segundo_apellido = segundo_apellido
    perfil.telefono = telefono
    perfil.estado = "activo" if i % 2 == 0 else "inactivo"
    perfil.save()

    print(f"✅ Usuario creado: {username}")
    creados += 1

print(f"\n✅ Total de usuarios creados: {creados}")
