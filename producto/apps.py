from django.apps import AppConfig


class ProductoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'producto'
    def ready(self):
        # Importar signals para registrar handlers
        try:
            import producto.signals  # noqa: F401
        except Exception:
            pass
