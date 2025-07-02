from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# ---------------------------
# Perfil del Usuario (extiende User)
# ---------------------------
class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto = models.ImageField(upload_to='avatars/', blank=True, null=True)
    segundo_nombre = models.CharField(max_length=50, blank=True)
    segundo_apellido = models.CharField(max_length=50, blank=True)
    telefono = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.user.email}"


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    try:
        instance.perfilusuario.save()
    except PerfilUsuario.DoesNotExist:
        PerfilUsuario.objects.create(user=instance)

# ---------------------------
# Control de Frecuencia (ON/OFF y valor)
# ---------------------------
class FrecuenciaControl(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    frecuencia = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.BooleanField(default=False)  # True = ON, False = OFF
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        estado_str = "ON" if self.estado else "OFF"
        return f"{self.usuario.username} - {self.frecuencia} Hz - {estado_str}"


# ---------------------------
# Log de Acciones
# ---------------------------
class LogAcciones(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    accion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fecha} - {self.usuario.username if self.usuario else 'Desconocido'} - {self.accion}"


# ---------------------------
# Registro de Usos del Jammer
# ---------------------------
class RegistroJammer(models.Model):
    usuario_inicio = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='registros_iniciados')
    usuario_fin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='registros_finalizados')
    frecuencia_mhz = models.DecimalField(max_digits=10, decimal_places=2)
    ubicacion = models.CharField(max_length=100, blank=True)
    inicio_registro = models.DateTimeField()
    fin_registro = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return (
            f"{self.usuario_inicio} ({self.frecuencia_mhz} MHz) "
            f"desde {self.inicio_registro} "
            f"hasta {self.fin_registro or 'Activo'}"
        )
