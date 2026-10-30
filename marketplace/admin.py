from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, FloristProfile, Category, Product, Cart, CartItem, Order, OrderItem, DeliveryInfo

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Marketplace", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "florist", "category", "price", "unit", "stock", "is_active", "created_at")
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("name", "florist__username", "description")
    list_editable = ("price", "stock", "is_active")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "florist", "product_name", "unit_price", "quantity", "fulfillment_status", "stock_restored")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer", "total_amount", "payment_method", "order_status", "created_at")
    list_filter = ("order_status", "payment_method", "created_at")
    search_fields = ("order_number", "customer__username", "customer__email")
    inlines = [OrderItemInline]
    readonly_fields = ("order_number", "total_amount", "order_status", "created_at")

admin.site.register([FloristProfile, Category, Cart, CartItem, OrderItem, DeliveryInfo])
