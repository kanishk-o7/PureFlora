"""Import the flower sample catalog originally shipped in js/data.js."""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from marketplace.models import Category, CustomUser, FloristProfile, Product

FLOWERS = [
    ("Blush Garden Roses", "Roses", 250, 48, "Meadow & Stem Farm", "https://images.unsplash.com/photo-1494972308805-463bc619d34e?auto=format&fit=crop&w=900&q=85", "Soft blush petals with a beautifully classic silhouette."),
    ("Velvet Red Roses", "Roses", 280, 32, "Rosewood Gardens", "https://images.unsplash.com/photo-1518895949257-7621c3c786d7?auto=format&fit=crop&w=900&q=85", "Rich red roses for bold, timeless arrangements."),
    ("White Oriental Lilies", "Lilies", 350, 22, "Meadow & Stem Farm", "https://images.unsplash.com/photo-1561181286-d3fee7d55364?auto=format&fit=crop&w=900&q=85", "Graceful white lilies with a fresh, clean finish."),
    ("Golden Marigolds", "Marigolds", 120, 80, "Sunpatch Collective", "https://images.unsplash.com/photo-1606041008023-472dfb5e530f?auto=format&fit=crop&w=900&q=85", "Sunshine-bright golden blooms, ideal for celebrations."),
    ("Pink Parrot Tulips", "Seasonal", 320, 18, "Petal Lane Farm", "https://images.unsplash.com/photo-1520763185298-1b434c919102?auto=format&fit=crop&w=900&q=85", "Sculptural, ruffled tulips with a soft spring feeling."),
    ("Sunrise Gerbera Mix", "Seasonal", 180, 40, "Sunpatch Collective", "https://images.unsplash.com/photo-1490750967868-88aa4486c946?auto=format&fit=crop&w=900&q=85", "A cheerful mix of bright, long-lasting gerberas."),
    ("Purple Dendrobium Orchids", "Exotic", 420, 12, "Orchid House", "https://images.unsplash.com/photo-1566907225472-4a9a4f1a9b4a?auto=format&fit=crop&w=900&q=85", "Distinctive orchid stems for elevated floral designs."),
    ("Cloud Baby's Breath", "Seasonal", 200, 28, "Petal Lane Farm", "https://images.unsplash.com/photo-1525310072745-f49212b5ac6d?auto=format&fit=crop&w=900&q=85", "Airy little white flowers for delicate arrangements."),
    ("Pink Lotus Stems", "Exotic", 300, 14, "Riverbend Flowers", "https://images.unsplash.com/photo-1508610048659-a06b669e3321?auto=format&fit=crop&w=900&q=85", "A striking specialty bloom with a serene, sculptural look."),
    ("Cream Chrysanthemums", "Seasonal", 160, 36, "Meadow & Stem Farm", "https://images.unsplash.com/photo-1508610048659-a06b669e3321?auto=format&fit=crop&w=900&q=85", "Full, soft blooms that bring texture to every bunch."),
    ("Peach Garden Roses", "Roses", 270, 26, "Rosewood Gardens", "https://images.unsplash.com/photo-1494972308805-463bc619d34e?auto=format&fit=crop&w=900&q=85", "Warm peach roses with a gentle, romantic tone."),
    ("Soft Pink Carnations", "Seasonal", 140, 0, "Petal Lane Farm", "https://images.unsplash.com/photo-1490750967868-88aa4486c946?auto=format&fit=crop&w=900&q=85", "Ruffled pink petals with a long-lasting vase life."),
]

class Command(BaseCommand):
    help = "Seed the database with the twelve flowers from the original Pure Flora frontend."

    def handle(self, *args, **options):
        florist_users = {}
        for name, category_name, price, stock, shop_name, image, description in FLOWERS:
            username = "sample_" + slugify(shop_name).replace("-", "_")
            florist = florist_users.get(shop_name)
            if florist is None:
                florist, created = CustomUser.objects.get_or_create(
                    username=username,
                    defaults={"role": "florist", "first_name": shop_name, "is_active": True},
                )
                if florist.role != "florist":
                    raise ValueError(f"The sample florist account {username!r} already exists with another role.")
                if created:
                    florist.set_unusable_password()
                    florist.save(update_fields=["password"])
                FloristProfile.objects.update_or_create(user=florist, defaults={"shop_name": shop_name})
                florist_users[shop_name] = florist

            category, _ = Category.objects.get_or_create(
                slug=slugify(category_name), defaults={"name": category_name}
            )
            if category.name != category_name:
                category.name = category_name
                category.save(update_fields=["name"])
            Product.objects.update_or_create(
                florist=florist,
                name=name,
                defaults={
                    "category": category,
                    "description": description,
                    "price": Decimal(price),
                    "image_url": image,
                    "unit": "bunch",
                    "stock": stock,
                    "is_active": True,
                },
            )

        self.stdout.write(self.style.SUCCESS(f"Imported {len(FLOWERS)} sample flower listings."))
