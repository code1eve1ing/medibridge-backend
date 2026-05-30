from django.apps import AppConfig


class PatientsConfig(AppConfig):
    name = "apps.patients"

    def ready(self):
        import apps.patients.signals  # noqa: F401
