# Importaciones de Django
from django.urls import path

# Importación de vistas locales
from . import views
# Importaciones de Django
from django.conf import settings
# Importaciones de Django
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('inicio/', views.inicio_view, name='inicio'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('alertas/', views.alertas_view, name='alertas'),
    path('usos/', views.usos_view, name='usos'),

    path('usuarios/', views.gestion_usuarios, name='usuarios'),
    path('usuarios/crear/', views.crear_usuario_modal_view, name='crear_usuario'),
    path('usuarios/editar/', views.editar_usuario_view, name='editar_usuario'),
    path('usuarios/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),

    path('usuarios/obtener/<int:user_id>/', views.obtener_usuario_json, name='obtener_usuario_json'),

    path('recuperar-password/', views.recuperar_password_view, name='recuperar_password'),

    path('usuarios/eliminar-multiples/', views.eliminar_usuarios, name='eliminar_usuarios'),
    path('usuarios/cambiar-estado/', views.cambiar_estado_usuarios, name='cambiar_estado_usuarios'),

    path('usos/exportar/csv/', views.exportar_usos_csv, name='exportar_usos_csv'),
    path('usos/exportar/pdf/', views.exportar_usos_pdf, name='exportar_usos_pdf'),

    path('alertas/exportar/csv/', views.exportar_alertas_csv, name='exportar_alertas_csv'),
    path('alertas/exportar/pdf/', views.exportar_alertas_pdf, name='exportar_alertas_pdf'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
