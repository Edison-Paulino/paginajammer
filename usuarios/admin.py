from django.contrib import admin
from django.utils.html import format_html
from .models import PerfilUsuario, FrecuenciaControl, LogAcciones

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'foto_miniatura', 'segundo_nombre', 'segundo_apellido', 'telefono')
    search_fields = ('user__username', 'user__email', 'telefono')
    readonly_fields = ('foto_miniatura',)

    def foto_miniatura(self, obj):
        if obj.foto:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 50%"/>', obj.foto.url)
        return "(Sin foto)"
    foto_miniatura.short_description = "Foto"

@admin.register(FrecuenciaControl)
class FrecuenciaControlAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'frecuencia', 'estado', 'fecha_modificacion')
    list_filter = ('estado', 'fecha_modificacion')
    search_fields = ('usuario__username', 'usuario__email')
    ordering = ('-fecha_modificacion',)

@admin.register(LogAcciones)
class LogAccionesAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'fecha')
    search_fields = ('usuario__username', 'accion')
    list_filter = ('fecha',)
    ordering = ('-fecha',)
