from django.apps import AppConfig


class EasyrideConfig(AppConfig):
    name = "EasyRide"

    def ready(self):
        from . import signals  # noqa: F401 — registra os receivers de invalidação de cache
