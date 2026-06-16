#!/usr/bin/env python
import os
import sys
from pathlib import Path

import django
# from timescale.tests import test_settings
from django.conf import settings
from django.test.utils import get_runner

if __name__ == '__main__':
    # settings.configure(default_settings=test_settings, DEBUG=True)
    # django.setup()
    # sys.path.append(Path(__file__).resolve().parent.as_posix())
    os.environ['DJANGO_SETTINGS_MODULE'] = 'timescale.tests.test_settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['timescale.tests.test_operations.TimescaleDBMigrationTest'])
    sys.exit(bool(failures))
