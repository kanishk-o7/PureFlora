from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('cart/', views.cart_view, name='cart'),
    path('api/products/', views.api_products, name='api_products'),
]
