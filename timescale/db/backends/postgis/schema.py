from ..timescaledb.schema import TimescaleBaseSchemaEditor
from django.contrib.gis.db.backends.postgis.schema import PostGISSchemaEditor


class TimescaleSchemaEditor(PostGISSchemaEditor, TimescaleBaseSchemaEditor):
    pass
