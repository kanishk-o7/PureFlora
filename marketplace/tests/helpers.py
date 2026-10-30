from decimal import Decimal
from marketplace.models import Category, CustomUser, FloristProfile, Product


def make_florist(username):
    user = CustomUser.objects.create_user(username=username, password="Fern-Cloud-742!", role="florist")
    FloristProfile.objects.create(user=user, shop_name=f"{username} Flowers")
    return user


def make_customer(username="customer"):
    return CustomUser.objects.create_user(username=username, password="Fern-Cloud-742!", role="customer")


def make_product(florist, name="Test Flower", stock=10, price="25.00", category_name="Roses"):
    category, _ = Category.objects.get_or_create(
        slug=category_name.lower().replace(" ", "-"), defaults={"name": category_name}
    )
    return Product.objects.create(
        florist=florist,
        category=category,
        name=name,
        description=f"Description for {name}",
        price=Decimal(price),
        image_url=f"https://example.com/{name.lower().replace(' ', '-')}.jpg",
        stock=stock,
    )
