import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pureflora.settings")

application = get_wsgi_application()

# Vercel instances have a writable temporary directory but no durable local disk.
# Create the demo SQLite schema when a fresh instance starts.
if os.environ.get("VERCEL") == "1":
    from django.core.management import call_command
    call_command("migrate", interactive=False, verbosity=0)
