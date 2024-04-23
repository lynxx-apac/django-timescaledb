from django.test import TestCase


class ModelTest(TestCase):
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
