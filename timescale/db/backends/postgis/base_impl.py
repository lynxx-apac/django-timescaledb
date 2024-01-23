import logging
import importlib
from django.conf import settings
from ..timescaledb.base_impl import schema_editor, introspection, operations
from django.db.backends.postgresql.base import DatabaseWrapper as PsycopgDatabaseWrapper
from django.core.exceptions import ImproperlyConfigured
logging = logging.getLogger(__name__)


def backend():
    """ override backend from timescaledb.base_impl to provide postgis as default backend base """
    base_class_name = getattr(settings, "TIMESCALE_DB_BACKEND_BASE", "django.contrib.gis.db.backends.postgis")
    base_class_module = importlib.import_module(base_class_name + ".base")
    base_class = getattr(base_class_module, "DatabaseWrapper", None)
    if not base_class:
        raise ImproperlyConfigured(
            (
                "'%s' is not a valid database back-end."
                " The module does not define a DatabaseWrapper class."
                " Check the value of TIMESCALE_EXTRA_DB_BACKEND_BASE."
            )
            % base_class_name
        )
    if isinstance(base_class, PsycopgDatabaseWrapper):
        raise ImproperlyConfigured(
            (
                "'%s' is not a valid database back-end."
                " It does inherit from the PostgreSQL back-end."
                " Check the value of TIMESCALE_EXTRA_DB_BACKEND_BASE."
            )
            % base_class_name
        )
    return base_class
