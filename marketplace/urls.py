from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"), path("products/", views.products, name="products"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path("products/<int:product_id>/orders/<int:order_id>/review/", views.add_review, name="add_review"),
    path("cart/", views.cart_view, name="cart"), path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/item/<int:item_id>/update/", views.update_cart_item, name="update_cart_item"),
    path("cart/item/<int:item_id>/remove/", views.remove_cart_item, name="remove_cart_item"),
    path("checkout/", views.checkout, name="checkout"), path("orders/<str:order_number>/success/", views.order_success, name="order_success"),
    path("orders/", views.order_history, name="order_history"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
    path("orders/<int:order_id>/cancel/", views.cancel_order, name="cancel_order"),
    path("accounts/register/", views.register, name="register"), path("accounts/login/", views.login_view, name="login"), path("accounts/logout/", views.logout_view, name="logout"),
    path("florist/", views.florist_dashboard, name="florist_dashboard"), path("florist/products/add/", views.product_create, name="product_create"),
    path("florist/profile/", views.florist_profile, name="florist_profile"),
    path("florist/products/<int:pk>/edit/", views.product_edit, name="product_edit"), path("florist/products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("florist/orders/", views.florist_orders, name="florist_orders"), path("florist/order-items/<int:item_id>/status/", views.florist_order_status, name="florist_order_status"),
    path("market-admin/", views.admin_dashboard, name="admin_dashboard"),
    path("tracking/", views.tracking, name="tracking"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/toggle/<int:product_id>/", views.wishlist_toggle, name="wishlist_toggle"),
    path("analytics/", views.analytics, name="analytics"),
]
