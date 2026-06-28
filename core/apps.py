from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
<<<<<<< HEAD
        pass
=======
        import core.signals
>>>>>>> df4708b9815261166538935075d15908a8cc5dfc
