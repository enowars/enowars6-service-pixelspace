"""
ASGI config for pixelspace project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from django.core.wsgi import get_wsgi_application
from a2wsgi import WSGIMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pixelspace.settings')

application = WSGIMiddleware(get_wsgi_application())
