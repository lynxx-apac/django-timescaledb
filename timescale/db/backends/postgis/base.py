import logging
from django.db import ProgrammingError
from django.db.migrations.state import ProjectState
from django.contrib.postgres.operations import CreateExtension

from . import base_impl
from .schema import TimescaleSchemaEditor


logger = logging.getLogger(__name__)


class DatabaseWrapper(base_impl.backend()):
    SchemaEditorClass = TimescaleSchemaEditor

    def prepare_database(self):
        """
        Prepare the configured database.
        This is where we enable the `timescaledb` extension if it isn't enabled yet.
        """
        super().prepare_database()
        # this comes from django/test/postgres_test/test_operations.py -> CreateExtensionTests
        app_label = "create_extension_dummy_app"
        operation = CreateExtension('timescaledb')
        project_state = ProjectState()
        new_state = project_state.clone()
        try:
            operation.database_forwards(app_label, self.client.connection.schema_editor(), new_state, project_state)
        except ProgrammingError:  # permission denied
            logger.warning(
                msg='''
                    Failed to create "timescaledb" extension. 
                    Usage of timescale capabilities might fail
                    If timescale is needed, make sure you are connected 
                    to the database as a superuser 
                    or add the extension manually.
                ''',
                exc_info=True
            )
