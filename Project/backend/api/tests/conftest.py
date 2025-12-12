import os
import django
from django.conf import settings
from django.core.management import call_command

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Use SQLite for tests instead of PostgreSQL
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',  # Use in-memory database for tests
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'api',
        ],
        SECRET_KEY='test-secret-key-for-ci',
        USE_TZ=True,
    )
else:
    # Override database settings for test environment
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

# Setup Django before any imports
django.setup()

# Create tables by running migrations
call_command('migrate', verbosity=0, interactive=False)
