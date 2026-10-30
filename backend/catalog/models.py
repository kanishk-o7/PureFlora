from django.db import models


class Product(models.Model):
    id = models.SlugField(primary_key=True, max_length=80)
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=80, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=80)
    stock = models.PositiveIntegerField(default=0)
    grower = models.CharField(max_length=160)
    tag = models.CharField(max_length=80, blank=True)
    color = models.CharField(max_length=40, blank=True)
    image = models.URLField(max_length=1000, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name
