"""
WSGI config for jms project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jms.settings')

application = get_wsgi_application()
