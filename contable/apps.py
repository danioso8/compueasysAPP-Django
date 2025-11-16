from django.apps import AppConfig


class ContableConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contable'
    
    def ready(self):
        import contable.signals  # Importar señales al iniciar la app
