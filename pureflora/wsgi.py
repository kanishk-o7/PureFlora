import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pureflora.settings")

application = get_wsgi_application()

# Vercel instances have a writable temporary directory but no durable local disk.
# Create the demo SQLite schema when a fresh instance starts.
if os.environ.get("VERCEL") == "1":
    from django.core.management import call_command
    call_command("migrate", interactive=False, verbosity=0)

    # Seed common choices so a fresh temporary Vercel database has categories
    # available in the florist product form and marketplace filters.
    from django.utils.text import slugify
    from marketplace.models import Category

    for category_name in (
        "Roses",
        "Lilies",
        "Tulips",
        "Orchids",
        "Carnations",
        "Gerberas",
        "Marigolds",
        "Chrysanthemums",
        "Sunflowers",
        "Jasmine",
        "Lotus",
        "Seasonal",
        "Exotic",
    ):
        Category.objects.get_or_create(
            slug=slugify(category_name), defaults={"name": category_name}
        )

    # Optional demo superuser bootstrap. Credentials stay in Vercel env vars,
    # never in source control. Temporary Vercel instances recreate this user.
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
    if username and password:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=os.environ.get("DJANGO_SUPERUSER_EMAIL", ""),
                password=password,
            )
