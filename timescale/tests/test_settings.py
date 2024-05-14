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
