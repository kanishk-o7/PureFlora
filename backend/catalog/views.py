from decimal import Decimal, InvalidOperation

from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def get_queryset(self):
        products = Product.objects.filter(is_active=True)
        params = self.request.query_params
        category = params.get("category")
        search = params.get("search", "").strip()

        if category and category.lower() != "all":
            products = products.filter(category__iexact=category)
        if search:
            products = products.filter(
                Q(name__icontains=search)
                | Q(category__icontains=search)
                | Q(grower__icontains=search)
                | Q(description__icontains=search)
            )
        if params.get("in_stock", "").lower() in ("1", "true", "yes"):
            products = products.filter(stock__gt=0)

        max_price = params.get("max_price")
        if max_price:
            try:
                products = products.filter(price__lte=Decimal(max_price))
            except InvalidOperation:
                products = products.none()
        return products
