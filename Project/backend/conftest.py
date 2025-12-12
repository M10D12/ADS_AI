"""
Configuração do pytest para o projeto Django
"""
import os
import django
from django.conf import settings

def pytest_configure():
    """Configura o Django antes de executar os testes"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
