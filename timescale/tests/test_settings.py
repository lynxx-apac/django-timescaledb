# import django.views.csrf

SECRET_KEY = 'fake-key'

INSTALLED_APPS = [
    'timescale.tests'
]

DATABASES = {
    'default': {
        'ENGINE': 'timescale.db.backends.postgresql',
        'NAME': 'iot_example_app',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

TIME_ZONE = 'UTC'
# LOGGING_CONFIG = None
# FORCE_SCRIPT_NAME = None
# DEFAULT_TABLESPACE = None
# ABSOLUTE_URL_OVERRIDES = {}
# ALLOWED_HOSTS = ['*']
# EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
# TEST_RUNNER = 'django.test.runner.DiscoverRunner'
# CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
# LOCALE_PATHS = []
# USE_I18N = True
# LANGUAGES = [('en', 'English')]
# LANGUAGE_CODE = 'en-us'
# LANGUAGES_BIDI = ''
# DATABASE_ROUTERS = {}
# STATIC_URL = '/static/'
# MEDIA_URL = '/media/'
# CSRF_TRUSTED_ORIGINS = ['http://localhost:8000']
# CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'
# SILENCED_SYSTEM_CHECKS = []
# TEMPLATES = []
# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {
#         "console": {
#             "class": "logging.StreamHandler",
#         },
#     },
#     "root": {
#         "handlers": ["console"],
#         "level": "WARNING",
#     },
# }
