import unittest
from django.test import SimpleTestCase, TestCase, modify_settings
from django.db import connection


class TimescaleDBExtensionTest(TestCase):
    def test_extension_installed(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM pg_available_extensions")
            self.assertTrue(cursor.rowcount > 0)




class TimescaleDBMigrationTest(unittest.TestCase):
    @property
    def app(self):
        return apps.get_containing_app_config(type(self).__module__).name

    migrate_from = None
    migrate_to = None

    def setUp(self):
        assert self.migrate_from and self.migrate_to, \
            f"TestCase '{type(self).__name__}' must define migrate_from and migrate_to properties"
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        # Reverse to the original migration
        executor.migrate(self.migrate_from)
        self.setUpBeforeMigration(old_apps)
        # Run the migration to test
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()  # reload.
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def setUpBeforeMigration(self, apps):
        pass


class ModelTest(unittest.TestCase):
    def _run_command(self, *args):
        from django.core.management import execute_from_command_line
        argv = ['manage.py'] + list(args)
        execute_from_command_line(argv)

    def create_hypertable(self):
        pass

    def create_aggregation(self):
        pass

    def create_retention(self):
        pass

    def create_compression(self):
        pass
