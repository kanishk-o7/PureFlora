from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "category",
            "price",
            "unit",
            "stock",
            "grower",
            "tag",
            "color",
            "image",
            "description",
        )
