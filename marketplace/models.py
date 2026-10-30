"""Marketplace data models. Order placement uses a database transaction for stock safety."""
import uuid
from django.db.models import Avg
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [("customer", "Customer"), ("florist", "Florist / Seller"), ("admin", "Admin")]
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default="customer")

    def save(self, *args, **kwargs):
        # Django staff accounts retain their admin role; ordinary account registration is customer/florist only.
        if self.is_superuser:
            self.role = "admin"
        super().save(*args, **kwargs)

class FloristProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="florist_profile")
    shop_name = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to="florists/", blank=True, null=True)
    def __str__(self): return self.shop_name or self.user.get_full_name() or self.user.username

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    def __str__(self): return self.name

class Product(models.Model):
    UNIT_CHOICES = [
        ("bunch", "Per Bunch"),
        ("stem", "Per Stem"),
        ("bouquet", "Per Bouquet"),
        ("box", "Per Box"),
    ]
    florist = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="products", limit_choices_to={"role": "florist"})
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=180)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="flowers/", blank=True, null=True)
    image_url = models.URLField(blank=True, help_text="Optional remote image URL used when no uploaded image is set.")
    unit = models.CharField(max_length=12, choices=UNIT_CHOICES, default="bunch")
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    @property
    def average_rating(self):
        average = self.reviews.aggregate(value=Avg("rating"))["value"]
        return round(average, 1) if average is not None else 0.0
    @property
    def total_reviews(self):
        return self.reviews.count()
    def get_image_url(self):
        """Prefer an uploaded image, then the retained remote URL, then a local placeholder."""
        if self.image:
            return self.image.url
        return self.image_url or "/static/images/flower-placeholder.svg"
    def __str__(self): return self.name

class Cart(models.Model):
    customer = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="cart")
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"Cart for {self.customer}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["cart", "product"], name="unique_product_per_cart")]
    def __str__(self): return f"{self.quantity} × {self.product.name}"
    @property
    def line_total(self): return self.product.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("confirmed", "Confirmed"), ("shipped", "Shipped"), ("delivered", "Delivered"), ("cancelled", "Cancelled"), ("partially_fulfilled", "Partially fulfilled")]
    PAYMENT_CHOICES = [("COD", "Cash on Delivery")]
    customer = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="orders")
    order_number = models.CharField(max_length=24, unique=True, editable=False)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=8, choices=PAYMENT_CHOICES, default="COD")
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = "PF-" + uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)
    def sync_fulfillment(self):
        """Aggregate vendor line statuses and exclude cancelled lines from COD total."""
        statuses = list(self.items.values_list("fulfillment_status", flat=True))
        if not statuses or all(status == "pending" for status in statuses):
            overall = "pending"
        elif all(status == "cancelled" for status in statuses):
            overall = "cancelled"
        elif all(status == "delivered" for status in statuses):
            overall = "delivered"
        elif all(status in {"shipped", "delivered"} for status in statuses):
            overall = "shipped"
        elif len(set(statuses)) == 1 and statuses[0] == "processing":
            overall = "confirmed"
        elif all(status in {"pending", "processing"} for status in statuses):
            overall = "confirmed" if "processing" in statuses else "pending"
        else:
            overall = "partially_fulfilled"
        # Calculate from price snapshots so later catalog price changes do not alter history.
        total = sum((item.unit_price * item.quantity for item in self.items.exclude(fulfillment_status="cancelled")), start=0)
        self.order_status = overall
        self.total_amount = total
        self.save(update_fields=["order_status", "total_amount"])
    def __str__(self): return self.order_number

class OrderItem(models.Model):
    FULFILLMENT_CHOICES = [("pending", "Pending"), ("processing", "Processing"), ("shipped", "Shipped"), ("delivered", "Delivered"), ("cancelled", "Cancelled")]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    florist = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="sold_order_items")
    product_name = models.CharField(max_length=180)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    fulfillment_status = models.CharField(max_length=12, choices=FULFILLMENT_CHOICES, default="pending")
    stock_restored = models.BooleanField(default=False, help_text="Prevents a cancellation from restoring the same inventory twice.")
    @property
    def line_total(self): return self.unit_price * self.quantity
    def __str__(self): return f"{self.quantity} × {self.product_name}"

class DeliveryInfo(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="delivery_info")
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=12)
    def __str__(self): return f"Delivery for {self.order.order_number}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reviews")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("customer", "product", "order")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rating}/5 review for {self.product} by {self.customer}"
