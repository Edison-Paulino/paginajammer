from django import forms
from django.contrib.auth import get_user_model
from .models import PerfilUsuario

User = get_user_model()

# -----------------------------
# Formulario para actualizar datos básicos del User
# -----------------------------
class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['username'].widget.attrs['style'] = 'background-color: #1e293b; color: white;'

# -----------------------------
# Formulario para el modelo PerfilUsuario
# -----------------------------
class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['foto', 'segundo_nombre', 'segundo_apellido', 'telefono']

# -----------------------------
# Formulario de Registro (para crear User + PerfilUsuario)
# -----------------------------
class RegistroForm(forms.Form):
    username = forms.CharField(label="Nombre de usuario", max_length=150, required=True)
    email = forms.EmailField(label="Correo electrónico", required=True)
    first_name = forms.CharField(label="Primer nombre", max_length=30, required=True)
    segundo_nombre = forms.CharField(label="Segundo nombre", max_length=50, required=False)
    last_name = forms.CharField(label="Primer apellido", max_length=30, required=True)
    segundo_apellido = forms.CharField(label="Segundo apellido", max_length=50, required=False)
    telefono = forms.CharField(label="Teléfono", max_length=15, required=False)
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput())
    confirm_password = forms.CharField(label="Repetir contraseña", widget=forms.PasswordInput())

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data
