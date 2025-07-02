from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.models import User
import configparser
import os
from datetime import datetime
from django.core.paginator import Paginator
from django.core.paginator import Paginator
from django.utils.http import urlencode


from paginajammer import utils_db_registros, utils_alertas_db
from paginajammer.utils_jammer_logs import leer_estado_actual, leer_historial_apagados

from .forms import PerfilForm, PerfilUsuarioForm, RegistroForm
from .models import PerfilUsuario

User = get_user_model()

INI_PATH = r'D:\django_project\paginajammer\paginajammer\CONFIG.INI'

# === AUTENTICACIÓN ===

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get("next", "inicio"))
        else:
            messages.error(request, "Credenciales inválidas", extra_tags='error_login')
    return render(request, "usuarios/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# === FUNCIONES AUXILIARES ===

def generar_username(nombre, apellido1, apellido2):
    base = (nombre[0] + apellido1[0] + (apellido2[0] if apellido2 else '')).lower()
    contador = 1
    while True:
        username = f"{base}{contador:02d}"
        if not User.objects.filter(username=username).exists():
            return username
        contador += 1


# === PÁGINAS ===

@login_required
def home_view(request):
    return redirect("inicio")


@login_required
def inicio_view(request):
    provincias = [
        "Distrito Nacional", "Azua", "Bahoruco", "Barahona", "Dajabón", "Duarte",
        "Elías Piña", "El Seibo", "Espaillat", "Hato Mayor", "Hermanas Mirabal",
        "Independencia", "La Altagracia", "La Romana", "La Vega", "María Trinidad Sánchez",
        "Monseñor Nouel", "Monte Cristi", "Monte Plata", "Pedernales", "Peravia",
        "Puerto Plata", "Samaná", "San Cristóbal", "San José de Ocoa", "San Juan",
        "San Pedro de Macorís", "Sánchez Ramírez", "Santiago", "Santiago Rodríguez",
        "Santo Domingo", "Valverde"
    ]

    if request.method == "POST":
        provincia = request.POST.get("provincia")
        if not provincia:
            messages.error(request, "Debe seleccionar una provincia.")
            return redirect("inicio")

        nueva_frecuencia_mhz = request.POST.get("frecuencia")
        nuevo_selector = "1" if request.POST.get("selector") == "1" else "0"

        try:
            nueva_frecuencia_hz = int(float(nueva_frecuencia_mhz) * 1_000_000)
        except (ValueError, TypeError):
            nueva_frecuencia_hz = 915000000

        datos_anteriores = cargar_configuracion_ini()
        anterior_selector = datos_anteriores.get("selector", "0")
        anterior_frecuencia_mhz = str(int(int(datos_anteriores.get("frecuencia", "915000000")) / 1_000_000))

        guardar_configuracion_ini(nueva_frecuencia_hz, nuevo_selector)

        # === Registro de uso ===
        if anterior_selector == "1":
            if nuevo_selector == "0":
                # Jammer se APAGÓ
                utils_db_registros.cerrar_todos_registros_abiertos(
                    usuario_fin=request.user.username,
                    fin_registro=datetime.now().isoformat()
                )
            elif anterior_frecuencia_mhz != nueva_frecuencia_mhz:
                # Cambió frecuencia
                utils_db_registros.cerrar_todos_registros_abiertos(
                    usuario_fin=request.user.username,
                    fin_registro=datetime.now().isoformat()
                )
                utils_db_registros.insertar_registro(
                    usuario_inicio=request.user.username,
                    frecuencia_mhz=float(nueva_frecuencia_mhz),
                    ubicacion=provincia,
                    inicio_registro=datetime.now().isoformat()
                )
        elif anterior_selector == "0" and nuevo_selector == "1":
            # Jammer se ENCENDIÓ
            utils_db_registros.cerrar_todos_registros_abiertos(
                usuario_fin=request.user.username,
                fin_registro=datetime.now().isoformat()
            )
            utils_db_registros.insertar_registro(
                usuario_inicio=request.user.username,
                frecuencia_mhz=float(nueva_frecuencia_mhz),
                ubicacion=provincia,
                inicio_registro=datetime.now().isoformat()
            )

        messages.success(request, "Parámetros guardados correctamente.")
        return redirect("inicio")

    # === GET ===
    datos = cargar_configuracion_ini()
    frecuencia = datos.get("frecuencia", "915000000")
    selector = datos.get("selector", "0")
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # 👉 Intenta precargar la ubicación si hay registro abierto y frecuencia coincide
    ubicacion = ""
    if selector == "1":
        registro_abierto = utils_db_registros.obtener_cualquier_registro_abierto()
        if registro_abierto:
            freq_registro = str(int(registro_abierto[2]))
            freq_actual = str(int(int(frecuencia) / 1_000_000))
            if freq_registro == freq_actual:
                ubicacion = registro_abierto[3]

    return render(request, "usuarios/inicio.html", {
        "frecuencia": int(int(frecuencia) / 1000000),
        "selector": selector,
        "fecha_hora": fecha_hora,
        "provincias": provincias,
        "provincia_seleccionada": ubicacion,
    })



@login_required
def alertas_view(request):
    estado = leer_estado_actual()
    selector = int(estado.get("selector", "0")) if estado else 0

    if selector == 1:
        historial_logs = leer_historial_apagados()
        for linea in historial_logs:
            if not utils_alertas_db.existe_alerta_descripcion(linea):
                utils_alertas_db.insertar_alerta(
                    titulo="Apagado inesperado detectado",
                    descripcion=linea,
                    nivel="WARN",
                    usuario="sistema"
                )

    alertas = utils_alertas_db.obtener_todas_alertas()

    page_size = int(request.GET.get('page_size', 25))
    paginator = Paginator(alertas, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    sort_by = request.GET.get('sort_by', 'fecha')
    order = request.GET.get('order', 'asc')
    page_size = int(request.GET.get('page_size', 10))

    alertas = utils_alertas_db.obtener_todas_alertas()

    # Función de clave de ordenamiento
    def sort_key(a):
        if sort_by == 'fecha':
            return a[4]
        elif sort_by == 'titulo':
            return a[1].lower()
        elif sort_by == 'descripcion':
            return a[2].lower()
        elif sort_by == 'nivel':
            return a[3].lower()
        elif sort_by == 'usuario':
            return (a[5] or '').lower()
        return a[4]

    # Ordenar
    alertas.sort(key=sort_key, reverse=(order == 'desc'))

    # Paginar como antes
    paginator = Paginator(alertas, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "usuarios/alertas.html", {
        'alertas': page_obj,
        'page_obj': page_obj,
        'page_size': page_size,
        'sort_by': sort_by,
        'order': order,
    })



@login_required
def usos_view(request):
    if request.user.is_staff:
        registros = utils_db_registros.obtener_todos_registros()
    else:
        registros = utils_db_registros.obtener_registros_por_usuario(request.user.username)

    # === Ordenamiento ===
    sort_by = request.GET.get('sort_by', 'inicio')
    order = request.GET.get('order', 'asc')
    page_size = int(request.GET.get('page_size', 10))

    # Función de clave de ordenamiento
    def sort_key(r):
        if sort_by == 'usuario_inicio':
            return (r[1] or '').lower()
        elif sort_by == 'usuario_fin':
            return (r[2] or '').lower()
        elif sort_by == 'frecuencia':
            return float(r[3]) if r[3] else 0
        elif sort_by == 'ubicacion':
            return (r[4] or '').lower()
        elif sort_by == 'inicio':
            return r[5]
        elif sort_by == 'fin':
            return r[6] or ''
        return r[5]

    registros.sort(key=sort_key, reverse=(order == 'desc'))

    # === Paginación ===
    paginator = Paginator(registros, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "usuarios/usos.html", {
        "registros": page_obj,
        "page_obj": page_obj,
        "page_size": page_size,
        "sort_by": sort_by,
        "order": order,
    })



@login_required
def perfil_view(request):
    user = request.user
    perfil = PerfilUsuario.objects.get(user=user)
    user_form = PerfilForm(instance=user)
    perfil_form = PerfilUsuarioForm(instance=perfil)

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "editar_foto" and "nueva_foto" in request.FILES:
            # Solo actualiza la foto, sin tocar nada más
            perfil.foto = request.FILES["nueva_foto"]
            perfil.save()
            messages.success(request, "Foto de perfil actualizada.")
            return redirect("perfil")

        elif accion == "eliminar_foto":
            if perfil.foto:
                perfil.foto.delete(save=True)
                messages.success(request, "Foto de perfil eliminada.")
            return redirect("perfil")

        elif accion == "guardar":
            # Actualiza todos los demás campos del perfil y usuario
            user_form = PerfilForm(request.POST, instance=user)
            perfil_form = PerfilUsuarioForm(request.POST, request.FILES, instance=perfil)

            if user_form.is_valid() and perfil_form.is_valid():
                user_form.save()
                perfil_form.save()
                messages.success(request, "Perfil actualizado.")
                return redirect("perfil")
            else:
                messages.error(request, "Verifica los campos ingresados.")

    return render(request, "usuarios/perfil.html", {
        "user": user,
        "perfil": perfil,
        "user_form": user_form,
        "perfil_form": perfil_form
    })

    


# === USUARIOS ===

from django.core.paginator import Paginator

@staff_member_required
def gestion_usuarios(request):
    usuarios = User.objects.all().select_related("perfilusuario")

    # === Ordenamiento ===
    sort_by = request.GET.get('sort_by', 'nombre')
    order = request.GET.get('order', 'asc')

    def sort_key(u):
        if sort_by == 'nombre':
            return (u.first_name.lower(), u.last_name.lower())
        elif sort_by == 'username':
            return u.username.lower()
        elif sort_by == 'email':
            return u.email.lower()
        elif sort_by == 'telefono':
            return (u.perfilusuario.telefono or '').lower()
        return (u.first_name.lower(), u.last_name.lower())

    usuarios = sorted(usuarios, key=sort_key, reverse=(order == 'desc'))

    # === Paginación ===
    page_size = int(request.GET.get('page_size', 10))
    paginator = Paginator(usuarios, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'usuarios/usuarios.html', {
        'usuarios': page_obj,
        'page_obj': page_obj,
        'page_size': page_size,
        'sort_by': sort_by,
        'order': order,
    })


@staff_member_required
@csrf_exempt
def crear_usuario_modal_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        segundo_nombre = request.POST.get("segundo_nombre")
        segundo_apellido = request.POST.get("segundo_apellido")
        email = request.POST.get("email")
        telefono = request.POST.get("telefono")
        password = request.POST.get("password")

        if first_name and last_name and email and password:
            if User.objects.filter(email=email).exists():
                messages.error(request, "El correo ya está en uso.")
                return redirect("usuarios")

            username = generar_username(first_name, last_name, segundo_apellido or "")
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password
            )
            PerfilUsuario.objects.update_or_create(
                user=user,
                defaults={
                    "segundo_nombre": segundo_nombre,
                    "segundo_apellido": segundo_apellido,
                    "telefono": telefono,
                }
            )
            messages.success(request, f"Usuario creado exitosamente: {username}")
        else:
            messages.error(request, "Faltan campos obligatorios")

    return redirect("usuarios")


@require_POST
@user_passes_test(lambda u: u.is_staff)
def editar_usuario_view(request):
    user_id = request.POST.get("usuario_id")
    try:
        usuario = User.objects.get(id=user_id)
        perfil = usuario.perfilusuario
    except User.DoesNotExist:
        messages.error(request, "Usuario no encontrado.")
        return redirect("usuarios")

    nuevo_first_name = request.POST.get("first_name")
    nuevo_last_name = request.POST.get("last_name")
    nuevo_segundo_apellido = request.POST.get("segundo_apellido")
    nuevo_segundo_nombre = request.POST.get("segundo_nombre")
    nuevo_email = request.POST.get("email")
    nuevo_telefono = request.POST.get("telefono")

    if User.objects.filter(email=nuevo_email).exclude(id=usuario.id).exists():
        messages.error(request, "Ya existe un usuario con ese correo electrónico.")
        return redirect("usuarios")

    usuario.first_name = nuevo_first_name
    usuario.last_name = nuevo_last_name
    usuario.email = nuevo_email
    usuario.save()

    perfil.segundo_apellido = nuevo_segundo_apellido
    perfil.segundo_nombre = nuevo_segundo_nombre
    perfil.telefono = nuevo_telefono
    perfil.save()

    messages.success(request, "Usuario actualizado correctamente.")
    return redirect("usuarios")


@staff_member_required
def eliminar_usuario(request):
    if request.method == "POST":
        user_id = request.POST.get("usuario_id")
        user = get_object_or_404(User, id=user_id)
        user.delete()
        messages.success(request, "Usuario eliminado exitosamente.")
    return redirect("usuarios")


@staff_member_required
def obtener_usuario_json(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        perfil = PerfilUsuario.objects.get(user=user)
        data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "segundo_nombre": perfil.segundo_nombre,
            "segundo_apellido": perfil.segundo_apellido,
            "telefono": perfil.telefono,
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({"error": "Usuario no encontrado"}, status=404)


def recuperar_password_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        nueva_password = request.POST.get('nueva_password')
        confirmar_password = request.POST.get('confirmar_password')

        if nueva_password != confirmar_password:
            messages.error(request, "Las contraseñas no coinciden.", extra_tags="error_login")
            return redirect('login')

        try:
            usuario = User.objects.get(username=username, email=email)
            if hasattr(usuario, 'perfilusuario') and usuario.perfilusuario.telefono == telefono:
                usuario.set_password(nueva_password)
                usuario.save()
                messages.success(request, "Contraseña actualizada correctamente.")
                return redirect('login')
            else:
                messages.error(request, "Datos incorrectos o incompletos.", extra_tags="error_login")
        except User.DoesNotExist:
            messages.error(request, "Usuario no encontrado.", extra_tags="error_login")

        return redirect('login')

    return redirect('login')


# === ARCHIVO .INI ===

def cargar_configuracion_ini():
    config = configparser.ConfigParser()
    config.read(INI_PATH)
    return dict(config['PARAMETROS']) if 'PARAMETROS' in config else {}


def guardar_configuracion_ini(frecuencia, selector):
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    if 'PARAMETROS' not in config:
        config['PARAMETROS'] = {}

    config['PARAMETROS']['frecuencia'] = str(frecuencia)
    config['PARAMETROS']['selector'] = str(selector)

    with open(INI_PATH, 'w') as configfile:
        config.write(configfile)
