from unittest import mock
from django.db import migrations


try:
    from django.contrib.postgres.operations import CreateExtension
except ImportError:
    CreateExtension = mock.Mock()


class Migration(migrations.Migration):
    operations = [
        CreateExtension("timescaledb"),
    ]
