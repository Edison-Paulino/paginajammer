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

import csv
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch



from django.template.loader import get_template
from xhtml2pdf import pisa

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
            perfil = getattr(user, 'perfilusuario', None)
            if perfil and perfil.estado == "inactivo":
                messages.error(request, "Este usuario está inactivo. Contacte al administrador.", extra_tags='error_login')
                return redirect("login")
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
    canales_wifi = [
        ("1", 2412), ("2", 2417), ("3", 2422), ("4", 2427),
        ("5", 2432), ("6", 2437), ("7", 2442), ("8", 2447),
        ("9", 2452), ("10", 2457), ("11", 2462), ("12", 2467),
        ("13", 2472), ("14", 2484),
    ]


    if request.method == "POST":
        provincia = request.POST.get("provincia")
        if not provincia:
            messages.error(request, "Debe seleccionar una provincia.")
            return redirect("inicio")

        nueva_frecuencia_mhz = request.POST.get("frecuency")
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

    # Intenta precargar la ubicación si hay registro abierto y frecuencia coincide
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
        "canales_wifi": canales_wifi,

    })

from usuarios.models import Alerta


@login_required
def alertas_view(request):
    alertas = list(Alerta.objects.all())

    # Filtros GET
    nombre_q = request.GET.get("titulo", "").strip().lower()
    descripcion_q = request.GET.get("descripcion", "").strip().lower()
    nivel_q = request.GET.get("nivel", "").strip().lower()
    codigo_q = request.GET.get("usuario", "").strip().lower()  # ahora es el código
    fecha_q = request.GET.get("fecha", "").strip()
    mostrar_filtros = request.GET.get("mostrar_filtros", "false")

    def parse_datetime_custom(valor):
        for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(valor.strip(), fmt)
            except ValueError:
                continue
        return None

    # Aplicar filtros
    if nombre_q:
        alertas = [a for a in alertas if nombre_q in a.nombre.lower()]
    if descripcion_q:
        alertas = [a for a in alertas if descripcion_q in a.descripcion.lower()]
    if nivel_q:
        alertas = [a for a in alertas if nivel_q in a.nivel.lower()]
    if codigo_q:
        alertas = [a for a in alertas if codigo_q in a.codigo.lower()]
    if fecha_q:
        if "-" in fecha_q:
            partes = fecha_q.split("-")
            fecha_min = parse_datetime_custom(partes[0])
            fecha_max = parse_datetime_custom(partes[1]) if len(partes) > 1 else None
            if fecha_min and fecha_max:
                alertas = [a for a in alertas if a.fecha and fecha_min <= a.fecha <= fecha_max]
        else:
            fecha_b = parse_datetime_custom(fecha_q)
            if fecha_b:
                alertas = [
                    a for a in alertas
                    if fecha_b.strftime("%d/%m/%Y") in a.fecha.strftime("%d/%m/%Y %H:%M:%S")
                    or fecha_b.strftime("%H:%M") in a.fecha.strftime("%H:%M:%S")
                ]

    # Ordenamiento
    sort_by = request.GET.get('sort_by', 'fecha')
    order = request.GET.get('order', 'asc')

    def sort_key(a):
        if sort_by == 'fecha': return a.fecha
        elif sort_by == 'titulo': return a.nombre.lower()
        elif sort_by == 'descripcion': return a.descripcion.lower()
        elif sort_by == 'nivel': return a.nivel.lower()
        elif sort_by == 'usuario': return a.codigo.lower()  # ahora es código
        return a.fecha

    alertas.sort(key=sort_key, reverse=(order == 'desc'))

    # Paginación
    page_size = int(request.GET.get('page_size', 10))
    paginator = Paginator(alertas, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "usuarios/alertas.html", {
        'alertas': page_obj,
        'page_obj': page_obj,
        'page_size': page_size,
        'sort_by': sort_by,
        'order': order,
        'titulo_q': nombre_q,
        'descripcion_q': descripcion_q,
        'nivel_q': nivel_q,
        'usuario_q': codigo_q,
        'fecha_q': fecha_q,
        'mostrar_filtros': mostrar_filtros,
    })



@login_required
def usos_view(request):
    if request.user.is_staff:
        registros = utils_db_registros.obtener_todos_registros()
    else:
        registros = utils_db_registros.obtener_registros_por_usuario(request.user.username)

    # Convertir fechas ISO a objetos datetime antes de filtrar
    for i, r in enumerate(registros):
        try:
            inicio = datetime.fromisoformat(r[5]) if r[5] else None
        except Exception:
            inicio = None
        try:
            fin = datetime.fromisoformat(r[6]) if r[6] else None
        except Exception:
            fin = None
        registros[i] = r[:5] + (inicio, fin)

    # === FILTROS GET ===
    usuario_inicio_q = request.GET.get("usuario_inicio", "").strip().lower()
    usuario_fin_q = request.GET.get("usuario_fin", "").strip().lower()
    frecuencia_q = request.GET.get("frecuencia", "").strip()
    ubicacion_q = request.GET.get("ubicacion", "").strip().lower()
    inicio_q = request.GET.get("inicio", "").strip()
    fin_q = request.GET.get("fin", "").strip()
    mostrar_filtros = request.GET.get("mostrar_filtros", "false")

    # Función para convertir texto a datetime con varios formatos
    def parse_datetime_custom(valor):
        for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(valor.strip(), fmt)
            except ValueError:
                continue
        return None

    def cumple_filtro(r):
        if usuario_inicio_q and usuario_inicio_q not in (r[1] or '').lower():
            return False
        if usuario_fin_q and usuario_fin_q not in (r[2] or '').lower():
            return False
        if frecuencia_q and frecuencia_q not in str(r[3]):
            return False
        if ubicacion_q and ubicacion_q not in (r[4] or '').lower():
            return False

        # Filtro por inicio
        if inicio_q:
            if "-" in inicio_q:
                partes = inicio_q.split("-")
                start = parse_datetime_custom(partes[0])
                end = parse_datetime_custom(partes[1]) if len(partes) > 1 else None
                if start and end:
                    if not (r[5] and start <= r[5] <= end):
                        return False
            else:
                fecha = parse_datetime_custom(inicio_q)
                if fecha:
                    if not r[5] or (
                        fecha.strftime("%d/%m/%Y") not in r[5].strftime("%d/%m/%Y %H:%M:%S") and
                        fecha.strftime("%H:%M") not in r[5].strftime("%H:%M:%S")
                    ):
                        return False

        # Filtro por fin
        if fin_q:
            if "-" in fin_q:
                partes = fin_q.split("-")
                start = parse_datetime_custom(partes[0])
                end = parse_datetime_custom(partes[1]) if len(partes) > 1 else None
                if start and end:
                    if not (r[6] and start <= r[6] <= end):
                        return False
            else:
                fecha = parse_datetime_custom(fin_q)
                if fecha:
                    if not r[6] or (
                        fecha.strftime("%d/%m/%Y") not in r[6].strftime("%d/%m/%Y %H:%M:%S") and
                        fecha.strftime("%H:%M") not in r[6].strftime("%H:%M:%S")
                    ):
                        return False

        return True

    registros = list(filter(cumple_filtro, registros))

    # === ORDENAMIENTO ===
    sort_by = request.GET.get('sort_by', 'inicio')
    order = request.GET.get('order', 'desc')
    page_size = int(request.GET.get('page_size', 10))

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

    # === PAGINACIÓN ===
    paginator = Paginator(registros, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Convertir en una lista modificable
    registros_visibles = list(page_obj)

    # Enmascarar usuarios si no es admin
    if not request.user.is_staff:
        for i, r in enumerate(registros_visibles):
            usuario_inicio = r[1]
            usuario_fin = r[2]

            usuario_inicio_visible = usuario_inicio if usuario_inicio == request.user.username else "Otro usuario"
            usuario_fin_visible = usuario_fin if usuario_fin == request.user.username else "Otro usuario"

            registros_visibles[i] = (
                r[0], usuario_inicio_visible, usuario_fin_visible, r[3], r[4], r[5], r[6]
            )
    else:
        registros_visibles = list(page_obj)


    context = {
        "registros": registros_visibles,  # <- ahora esta es la lista final
        "page_obj": page_obj,
        "page_size": page_size,
        "sort_by": sort_by,
        "order": order,
        "usuario_inicio_q": usuario_inicio_q,
        "usuario_fin_q": usuario_fin_q,
        "frecuencia_q": frecuencia_q,
        "ubicacion_q": ubicacion_q,
        "inicio_q": inicio_q,
        "fin_q": fin_q,
        "mostrar_filtros": mostrar_filtros,
    }

    if request.headers.get('Hx-Request') == 'true':
        return render(request, "usuarios/fragmento_tabla_usos.html", context)

    return render(request, "usuarios/usos.html", context)



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
        elif sort_by == 'estado':
            return (u.perfilusuario.estado or '').lower()
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


@user_passes_test(lambda u: u.is_staff)
def deshabilitar_usuario(request, id):
    usuario = get_object_or_404(User, id=id)
    if usuario.is_superuser:
        messages.error(request, "No puedes deshabilitar al superusuario.")
        return redirect('usuarios')
    usuario.is_active = False
    usuario.save()
    messages.success(request, f"Usuario '{usuario.username}' deshabilitado.")
    return redirect('usuarios')

@user_passes_test(lambda u: u.is_staff)
def habilitar_usuario(request, id):
    usuario = get_object_or_404(User, id=id)
    usuario.is_active = True
    usuario.save()
    messages.success(request, f"Usuario '{usuario.username}' habilitado.")
    return redirect('usuarios')


@require_POST
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def eliminar_usuarios(request):
    import json
    data = json.loads(request.body)
    ids = data.get('ids', [])
    User.objects.filter(id__in=ids).delete()
    return JsonResponse({'status': 'ok'})


@require_POST
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def cambiar_estado_usuarios(request):
    import json
    data = json.loads(request.body)
    ids = data.get('ids', [])
    for user in User.objects.filter(id__in=ids):
        perfil = getattr(user, 'perfilusuario', None)
        if perfil:
            perfil.estado = 'inactivo' if perfil.estado == 'activo' else 'activo'
            perfil.save()
    return JsonResponse({'status': 'ok'})



def formatear_fecha(fecha):
    if not fecha:
        return ''
    try:
        return datetime.fromisoformat(str(fecha)).strftime("%d/%m/%Y %H:%M:%S")
    except:
        return str(fecha)



@login_required
def exportar_usos_csv(request):
    registros = utils_db_registros.obtener_todos_registros() if request.user.is_staff else utils_db_registros.obtener_registros_por_usuario(request.user.username)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="usos.csv"'
    writer = csv.writer(response)
    writer.writerow(['Usuario Inicio', 'Usuario Fin', 'Frecuencia MHz', 'Ubicación', 'Inicio', 'Fin'])

    for r in registros:
        usuario_inicio = r[1] if request.user.is_staff or r[1] == request.user.username else "Otro usuario"
        usuario_fin = r[2] if request.user.is_staff or r[2] == request.user.username else "Otro usuario"
        writer.writerow([
            usuario_inicio, usuario_fin, r[3], r[4],
            formatear_fecha(r[5]), formatear_fecha(r[6]) or 'Activo'
        ])
    return response




@login_required
def exportar_usos_pdf(request):
    registros_raw = utils_db_registros.obtener_todos_registros() if request.user.is_staff else utils_db_registros.obtener_registros_por_usuario(request.user.username)

    def formatear_fecha(f):
        from datetime import datetime
        if not f: return ""
        try: return datetime.fromisoformat(str(f)).strftime("%d/%m/%Y %H:%M:%S")
        except: return str(f)

    registros = []
    for r in registros_raw:
        usuario_inicio = r[1] if request.user.is_staff or r[1] == request.user.username else "Otro usuario"
        usuario_fin = r[2] if request.user.is_staff or r[2] == request.user.username else "Otro usuario"
        registros.append({
            "usuario_inicio": usuario_inicio,
            "usuario_fin": usuario_fin,
            "frecuencia": r[3],
            "ubicacion": r[4],
            "inicio": formatear_fecha(r[5]),
            "fin": formatear_fecha(r[6]) or "Activo"
        })

    template = get_template("pdf/uso_exportado.html")
    html = template.render({"registros": registros, "now": datetime.now().strftime("%d/%m/%Y %H:%M:%S")})


    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="usos.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Hubo un error generando el PDF", status=500)

    return response


@login_required
def exportar_alertas_csv(request):
    alertas = utils_alertas_db.obtener_todas_alertas()

    if not request.user.is_staff:
        alertas = [(a[0], a[1], a[2], a[3], a[4], "Otro usuario" if a[5] != request.user.username else a[5]) for a in alertas]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="alertas.csv"'
    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Título', 'Descripción', 'Nivel', 'Usuario'])

    for a in alertas:
        fecha_str = a[4] if isinstance(a[4], str) else a[4].strftime("%d/%m/%Y %H:%M:%S")

        writer.writerow([fecha_str, a[1], a[2], a[3], a[5]])
    return response


@login_required
def exportar_alertas_pdf(request):
    alertas_raw = utils_alertas_db.obtener_todas_alertas()
    alertas = []

    for a in alertas_raw:
        fecha_str = a[4] if isinstance(a[4], str) else a[4].strftime("%d/%m/%Y %H:%M:%S")

        usuario = a[5] if request.user.is_staff or a[5] == request.user.username else "Otro usuario"
        alertas.append({
            "titulo": a[1],
            "descripcion": a[2],
            "nivel": a[3],
            "fecha": fecha_str,
            "usuario": usuario
        })

    template = get_template("pdf/alertas_exportado.html")
    html = template.render({"alertas": alertas, "now": datetime.now().strftime("%d/%m/%Y %H:%M:%S")})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="alertas.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Hubo un error generando el PDF", status=500)

    return response
