import django
django.setup()

from paginajammer.monitor.launch_monitor import iniciar_monitor

try:
    print("✅ Monitor de alertas activo")
    iniciar_monitor()
except Exception as e:
    print(f"❌ Error iniciando monitor de alertas (ASGI): {e}")
